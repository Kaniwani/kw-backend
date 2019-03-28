import random

from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from rest_framework.authtoken.models import Token

from kw_webapp import constants
from kw_webapp.models import (
    UserSpecific,
    Profile,
    Reading,
    Tag,
    Vocabulary,
    MeaningSynonym,
    AnswerSynonym,
    PartOfSpeech,
    Level,
    logger,
)
from kw_webapp.tasks import (
    has_multiple_kanji,
)
from kw_webapp.wanikani import make_api_call
from kw_webapp.tests.utils import create_review_for_specific_time


def wipe_all_reviews_for_user(user):
    reviews = UserSpecific.objects.filter(user=user)
    reviews.delete()
    if len(reviews) > 0:
        raise ValueError
    else:
        print("deleted all reviews for " + user.username)


def reset_reviews_for_user(user):
    reviews = UserSpecific.objects.filter(user=user)
    reviews.update(needs_review=False)
    reviews.update(last_studied=timezone.now())


def flag_all_reviews_for_user(user, needed):
    reviews = UserSpecific.objects.filter(user=user)
    reviews.update(needs_review=needed)


def reset_unlocked_levels_for_user(user):
    p = Profile.objects.get(user=user)
    p.unlocked_levels.clear()
    p.unlocked_levels.get_or_create(level=p.level)


def reset_user(user):
    wipe_all_reviews_for_user(user)
    reset_unlocked_levels_for_user(user)


def create_profile_for_user(user):
    p = Profile(user=user, api_key="INVALID_KEY", level=1, api_valid=False)
    p.save()
    return p


def correct_next_review_dates():
    us = UserSpecific.objects.all()
    i = 0
    for u in us:
        u.set_next_review_time_based_on_last_studied()
        print(i, u)


def create_new_review_and_merge_existing(vocabulary, found_vocabulary):
    print("New vocabulary id is:[{}]".format(vocabulary.id))
    print(
        "Old vocabulary items had meanings:[{}] ".format(
            " -> ".join(
                found_vocabulary.exclude(id=vocabulary.id).values_list(
                    "meaning", flat=True
                )
            )
        )
    )
    print(
        "Old vocabulary items had ids:[{}] ".format(
            " -> ".join(
                [
                    str(a)
                    for a in found_vocabulary.exclude(id=vocabulary.id).values_list(
                        "id", flat=True
                    )
                ]
            )
        )
    )
    ids = found_vocabulary.values_list("id").exclude(id=vocabulary.id)
    for user in User.objects.all():
        old_reviews = UserSpecific.objects.filter(user=user, vocabulary__in=ids)
        if old_reviews.count() > 0:
            print(
                "User [{}] had [{}] reviews which used one of the now merged vocab.".format(
                    user.username, old_reviews.count()
                )
            )
            print("Giving them a review for our new vocabulary object...")
            new_review = UserSpecific.objects.create(vocabulary=vocabulary, user=user)
            # Go over all the reviews which were duplicates, and pick the best one as the new accurate one.
            for old_review in old_reviews:
                if old_review.streak > new_review.streak:
                    print(
                        "Old review [{}] has new highest streak: [{}]".format(
                            old_review.id, old_review.streak
                        )
                    )
                    copy_review_data(new_review, old_review)
                else:
                    print(
                        "Old review [{}] has lower streak than current maximum.: [{}] < [{}]".format(
                            old_review.id, old_review.streak, new_review.streak
                        )
                    )
                if new_review.notes is None:
                    new_review.notes = old_review.notes
                else:
                    new_review.notes = new_review.notes + ", " + old_review.notes

                # slap all the synonyms found onto the new review.
                MeaningSynonym.objects.filter(review=old_review).update(
                    review=new_review
                )
                AnswerSynonym.objects.filter(review=old_review).update(
                    review=new_review
                )

            new_review.save()


def generate_user_stats(user):
    reviews = UserSpecific.objects.filter(user=user)
    kanji_review_map = {}
    for review in reviews:
        for reading in review.vocabulary.readings.all():
            if reading.character in kanji_review_map.keys():
                kanji_review_map[reading.character].append(review)
            else:
                kanji_review_map[reading.character] = []
                kanji_review_map[reading.character].append(review)

    print("Printing all duplicates for user.")
    for kanji, reviews in kanji_review_map.items():
        if len(reviews) > 1:
            print("***" + kanji + "***")
            for review in reviews:
                print(review)
    print("Finished printing duplicates")

def blow_away_duplicate_reviews_for_all_users():
    users = User.objects.filter(profile__isnull=False)
    for user in users:
        blow_away_duplicate_reviews_for_user(user)


def blow_away_duplicate_reviews_for_user(user):
    dupe_revs = (
        UserSpecific.objects.filter(user=user)
        .values("vocabulary")
        .annotate(num_reviews=Count("vocabulary"))
        .filter(num_reviews__gt=1)
    )

    if dupe_revs.count() > 0:
        print("Duplicate reviews found for user: ".format(dupe_revs.count()))
    vocabulary_ids = []
    for dupe_rev in dupe_revs:
        vocabulary_ids.append(dupe_rev["vocabulary"])

    print("Here are the vocabulary IDs we are gonna check: {}".format(vocabulary_ids))
    for voc_id in vocabulary_ids:
        review_id_to_save = UserSpecific.objects.filter(
            vocabulary__id=voc_id, user=user
        ).values_list("id", flat=True)[0]
        UserSpecific.objects.filter(vocabulary__id=voc_id, user=user).exclude(
            pk=int(review_id_to_save)
        ).delete()
        new_reviews = UserSpecific.objects.filter(vocabulary__id=voc_id, user=user)
        print("New review count: {}".format(new_reviews.count()))
        assert new_reviews.count() == 1


def one_time_import_jisho(json_file_path):
    import json

    with open(json_file_path) as file:
        with open("outfile.txt", "w") as outfile:
            parsed_json = json.load(file)

            for vocabulary_json in parsed_json:
                try:
                    related_reading = Reading.objects.get(
                        character=vocabulary_json["ja"]["characters"]
                    )
                    outfile.write(merge_with_model(related_reading, vocabulary_json))
                except Reading.DoesNotExist:
                    pass
                except Reading.MultipleObjectsReturned:
                    readings = Reading.objects.filter(
                        character=vocabulary_json["ja"]["characters"]
                    )
                    print("FOUND MULTIPLE READINGS")
                    for reading in readings:
                        print(
                            reading.vocabulary.meaning,
                            reading.character,
                            reading.kana,
                            reading.level,
                        )
                        merge_with_model(reading, vocabulary_json)


def one_time_import_jisho_new_format(json_file_path):
    import json

    no_local_vocab = []
    with open(json_file_path) as file:
        with open("outfile.txt", "w") as outfile:
            parsed_json = json.load(file)

            for vocabulary_json in parsed_json:
                try:
                    related_reading = Reading.objects.get(
                        character=vocabulary_json["character"]
                    )
                    outfile.write(merge_with_model(related_reading, vocabulary_json))
                except Reading.DoesNotExist:
                    no_local_vocab.append(vocabulary_json)
                    pass
                except Reading.MultipleObjectsReturned:
                    readings = Reading.objects.filter(
                        character=vocabulary_json["character"]
                    )
                    print("FOUND MULTIPLE READINGS")
                    for reading in readings:
                        if reading.kana == vocabulary_json["reading"]:
                            print(
                                reading.vocabulary.meaning,
                                reading.character,
                                reading.kana,
                                reading.level,
                            )
                            merge_with_model(reading, vocabulary_json)

    unfilled_vocabulary = Vocabulary.objects.exclude(
        readings__sentence_en__isnull=False
    )
    if unfilled_vocabulary.count() == 0:
        print("No missing information!")
    else:
        print("Missing some info!")
        for vocab in unfilled_vocabulary:
            print(vocab)
    print("Found no local vocabulary for: ")
    print(no_local_vocab)


def merge_with_model(related_reading, vocabulary_json):
    if related_reading.kana != vocabulary_json["reading"]:
        print("Not the primary reading, skipping: {}".format(related_reading.kana))
    else:
        print("Found primary Reading: {}".format(related_reading.kana))
    retval = "******\nWorkin on related reading...{},{}".format(
        related_reading.character, related_reading.id
    )
    retval += str(vocabulary_json)

    if "common" in vocabulary_json:
        related_reading.common = vocabulary_json["common"]
    else:
        retval += "NO COMMON?!"

    related_reading.isPrimary = True

    if "furi" in vocabulary_json:
        related_reading.furigana = vocabulary_json["furi"]

    if "pitch" in vocabulary_json:
        if len(vocabulary_json["pitch"]) > 0:
            string_pitch = ",".join([str(pitch) for pitch in vocabulary_json["pitch"]])
            related_reading.pitch = string_pitch

    if "partOfSpeech" in vocabulary_json:
        related_reading.parts_of_speech.clear()
        for pos in vocabulary_json["partOfSpeech"]:
            part = PartOfSpeech.objects.get_or_create(part=pos)[0]
            if part not in related_reading.parts_of_speech.all():
                related_reading.parts_of_speech.add(part)

    if "sentenceEn" in vocabulary_json:
        related_reading.sentence_en = vocabulary_json["sentenceEn"]

    if "sentenceJa" in vocabulary_json:
        related_reading.sentence_ja = vocabulary_json["sentenceJa"]

    related_reading.save()
    retval += "Finished with reading [{}]! Tags:{},".format(
        related_reading.id, related_reading.tags.count()
    )
    print(retval)
    return retval


def associate_tags(reading, tag):
    print("associating [{}] to reading {}".format(tag, reading.vocabulary.meaning))
    tag_obj, created = Tag.objects.get_or_create(name=tag)
    reading.tags.add(tag_obj)


def create_tokens_for_all_users():
    for user in User.objects.all():
        Token.objects.get_or_create(user=user)


def create_various_future_reviews_for_user(user):
    now = timezone.now()
    now = now.replace(minute=59)
    for i in range(0, 24):
        for j in range(0, 20):
            review = create_review_for_specific_time(
                user, str(i) + "-" + str(j), now + timezone.timedelta(hours=i)
            )

            review.streak = random.randint(1, 8)
            review.save()
            review.refresh_from_db()
            print(review)


def survey_conglomerated_vocabulary():
    count = 0
    for vocab in Vocabulary.objects.all():
        if has_multiple_kanji(vocab):
            print("Found item with multiple Kanji:[{}]".format(vocab.meaning))
            print(
                "\n".join(
                    reading.kana + ": " + reading.character
                    for reading in vocab.readings.all()
                )
            )
            count += 1

    print("total count:{}".format(count))


def find_all_duplicates():
    all_vocab = Vocabulary.objects.all()
    kanji_review_map = {}
    for vocab in all_vocab:
        for reading in vocab.readings.all():
            if reading.character in kanji_review_map.keys():
                kanji_review_map[reading.character].append(vocab)
            else:
                kanji_review_map[reading.character] = []
                kanji_review_map[reading.character].append(vocab)

    print("Printing all duplicates for all vocab.")
    duplicate_count = 0
    for kanji, vocabs in kanji_review_map.items():
        if len(vocabs) > 1:
            duplicate_count += 1
            print("***" + kanji + "***")
            for vocab in vocabs:

                print(vocab)
    print("Finished printing duplicates: found {}".format(duplicate_count))


def copy_review_data(new_review, old_review):
    print("Copying review data from [{}] -> [{}]".format(old_review.id, new_review.id))
    new_review.streak = old_review.streak
    new_review.incorrect = old_review.incorrect
    new_review.correct = old_review.correct
    new_review.next_review_date = old_review.next_review_date
    new_review.last_studied = old_review.last_studied
    new_review.burned = old_review.burned
    new_review.needs_review = old_review.needs_review
    new_review.wanikani_srs = old_review.wanikani_srs
    new_review.wanikani_srs_numeric = old_review.wanikani_srs_numeric
    new_review.wanikani_burned = old_review.wanikani_burned
    new_review.critical = old_review.critical
    new_review.unlock_date = old_review.unlock_date


def one_time_orphaned_level_clear():
    levels = Level.objects.filter(profile=None)
    levels.delete()


def has_multiple_kanji(vocab):
    kanji = [reading.character for reading in vocab.readings.all()]
    kanji2 = set(kanji)
    return len(kanji2) > 1

def add_subject_ids():
    from wanikani_api.client import Client
    from kw_webapp.tasks import get_vocab_by_kanji
    client = Client("2510f001-fe9e-414c-ba19-ccf79af40060")
    subjects = client.subjects(fetch_all=True, types="vocabulary", hidden=False)
    total_subs = len(subjects)
    match_count = 0
    no_local_equivalent = []
    for subject in subjects:
        try:
            local_vocabulary = get_vocab_by_kanji(subject.characters)
            local_vocabulary.wk_subject_id = subject.id
            local_vocabulary.reconcile(subject)
            match_count += 1
            logger.info(f"{match_count}/{total_subs}:\t{subject.characters}")
        except Vocabulary.DoesNotExist as e:
            no_local_equivalent.append(subject)

    unmatched = Vocabulary.objects.filter(wk_subject_id=0)
    return unmatched, no_local_equivalent


def repopulate():
    """
    A task that uses my personal API key in order to re-sync the database. Koichi often decides to switch things around
    on a level-per-level basis, or add synonyms, or change which readings are allowed. This method attempts to synchronize
    our data sets.

    :return:
    """
    url = "https://www.wanikani.com/api/user/" + constants.API_KEY + "/vocabulary/{}"
    logger.info("Starting DB Repopulation from WaniKani")
    for level in range(constants.LEVEL_MIN, constants.LEVEL_MAX + 1):
        json_data = make_api_call(url.format(level))
        vocabulary_list = json_data["requested_information"]
        for vocabulary in vocabulary_list:
            import_vocabulary_from_json(vocabulary)


def clear_duplicate_meaning_synonyms_from_reviews():
    # Fetch all reviews wherein there are duplicate meaning synonyms.
    reviews = (
        UserSpecific.objects.values("id", "meaning_synonyms__text")
        .annotate(Count("meaning_synonyms__text"))
        .filter(meaning_synonyms__text__count__gt=1)
    )
    review_list = list(reviews)
    review_list = set([review["id"] for review in review_list])

    for review_id in review_list:
        seen_synonyms = set()
        synonyms = MeaningSynonym.objects.filter(review=review_id)
        for synonym in synonyms:
            if synonym.text in seen_synonyms:
                print("[{}]Deleted element{}".format(review_id, synonym.text))
                synonym.delete()
            else:
                print(
                    "[{}]First time seeing element {}".format(review_id, synonym.text)
                )
                seen_synonyms.add(synonym.text)


def clear_duplicate_answer_synonyms_from_reviews():
    # Fetch all reviews wherein there are duplicate meaning synonyms.
    reviews = (
        UserSpecific.objects.values(
            "id", "reading_synonyms__kana", "reading_synonyms__character"
        )
        .annotate(Count("reading_synonyms__kana"))
        .filter(reading_synonyms__kana__count__gt=1)
    )
    review_list = list(reviews)
    review_list = set([review["id"] for review in review_list])

    for review_id in review_list:
        seen_synonyms = set()
        synonyms = AnswerSynonym.objects.filter(review=review_id)
        for synonym in synonyms:
            if synonym.kana + "_" + synonym.character in seen_synonyms:
                print(
                    "[{}]Deleted element: {}".format(
                        review_id, synonym.kana + "_" + synonym.character
                    )
                )
                synonym.delete()
            else:
                print(
                    "[{}]First time seeing element: {}".format(
                        review_id, synonym.kana + "_" + synonym.character
                    )
                )
                seen_synonyms.add(synonym.kana + "_" + synonym.character)
