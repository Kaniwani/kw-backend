from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token

from kw_webapp import constants
from kw_webapp.models import UserSpecific, Profile, Reading, Tag, Vocabulary, MeaningSynonym, AnswerSynonym
from kw_webapp.tasks import create_new_vocabulary, \
    has_multiple_kanji
from kw_webapp.wanikani import make_api_call


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


def one_time_merger():
    conglomerate_count = 0
    total_vocab_count = 0
    for level in range(1, 61):
        api_call = "https://www.wanikani.com/api/user/{}/vocabulary/{}".format(constants.API_KEY, level)
        response = make_api_call(api_call)
        vocab_list = response['requested_information']
        total_vocab_count += len(vocab_list)
        print("Vocab found:{}".format(len(vocab_list)))

        for vocabulary_json in vocab_list:
            print("**************************************************************")
            print("Analyzing vocab with kanji:[{}]\tCanonical meaning is:[{}]".format(vocabulary_json['character'],
                                                                                      vocabulary_json['meaning']))
            found_vocabulary = Vocabulary.objects.filter(readings__character=vocabulary_json['character'])
            print("found [{}] vocabulary on the server with kanji [{}]".format(found_vocabulary.count(),
                                                                               vocabulary_json['character']))
            if found_vocabulary.count() == 1 and found_vocabulary[0].meaning == vocabulary_json['meaning']:
                print("No conflict found. Precisely 1 vocab on server, and meaning matches.")
            elif found_vocabulary.count() > 1:
                conglomerate_count += 1
                print("Conflict found. Precisely [{}] vocab on server for meaning [{}].".format(found_vocabulary.count(),
                                                                                                vocabulary_json['meaning']))
                handle_merger(vocabulary_json, found_vocabulary)
    print("total vocabb count: {}".format(total_vocab_count))
    print("Conglomerates: {}".format(conglomerate_count))


def create_new_review_and_merge_existing(vocabulary, found_vocabulary):
    print("New vocabulary id is:[{}]".format(vocabulary.id))
    print("Old vocabulary items had meanings:[{}] ".format(
        " -> ".join(found_vocabulary.exclude(id=vocabulary.id).values_list('meaning', flat=True))))
    print("Old vocabulary items had ids:[{}] ".format(
        " -> ".join([str(a) for a in found_vocabulary.exclude(id=vocabulary.id).values_list('id', flat=True)])))
    ids = found_vocabulary.values_list('id').exclude(id=vocabulary.id)
    for user in User.objects.all():
        old_reviews = UserSpecific.objects.filter(user=user, vocabulary__in=ids)
        if old_reviews.count() > 0:
            print("User [{}] had [{}] reviews which used one of the now merged vocab.".format(user.username,
                                                                                              old_reviews.count()))
            print("Giving them a review for our new vocabulary object...")
            new_review = UserSpecific.objects.create(vocabulary=vocabulary, user=user)
            # Go over all the reviews which were duplicates, and pick the best one as the new accurate one.
            for old_review in old_reviews:
                if old_review.streak > new_review.streak:
                    print("Old review [{}] has new highest streak: [{}]".format(old_review.id, old_review.streak))
                    copy_review_data(new_review, old_review)
                else:
                    print("Old review [{}] has lower streak than current maximum.: [{}] < [{}]".format(old_review.id,
                                                                                                       old_review.streak,
                                                                                                       new_review.streak))
                if new_review.notes is None:
                    new_review.notes = old_review.notes
                else:
                    new_review.notes = new_review.notes + ", " + old_review.notes

                # slap all the synonyms found onto the new review.
                MeaningSynonym.objects.filter(review=old_review).update(review=new_review)
                AnswerSynonym.objects.filter(review=old_review).update(review=new_review)

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


def handle_merger(vocabulary_json, found_vocabulary):
    ids_to_delete = found_vocabulary.values_list('id', flat=True)
    tbd = []
    for id in ids_to_delete:
        tbd.append(id)

    print("Prepping ids to delete: {}".format(tbd))
    vocabulary = create_new_vocabulary(vocabulary_json)
    create_new_review_and_merge_existing(vocabulary, found_vocabulary)
    Vocabulary.objects.filter(pk__in=ids_to_delete).exclude(id=vocabulary.id).delete()


def one_time_import_jisho(json_file_path):
    import json
    with open(json_file_path) as file:
        with open("outfile.txt", 'w') as outfile:
            parsed_json = json.load(file)

            for vocabulary_json in parsed_json:
                try:
                    related_reading = Reading.objects.get(character=vocabulary_json["ja"]["characters"])
                    outfile.write(merge_with_model(related_reading, vocabulary_json))
                except Reading.DoesNotExist:
                    pass
                except Reading.MultipleObjectsReturned:
                    readings = Reading.objects.filter(character=vocabulary_json["ja"]["characters"])
                    print("FOUND MULTIPLE READINGS")
                    for reading in readings:
                        print(reading.vocabulary.meaning, reading.character, reading.kana, reading.level)
                        merge_with_model(reading, vocabulary_json)


def merge_with_model(related_reading, vocabulary_json):
    retval = "******\nWorkin on related reading...{},{}".format(related_reading.character, related_reading.id)
    retval += str(vocabulary_json)

    tags_json = vocabulary_json['tags']
    [associate_tags(related_reading, tag_json) for tag_json in tags_json]

    if "common" in vocabulary_json:
        related_reading.common = vocabulary_json["common"]
    else:
        retval += "NO COMMON?!"
    if "jlpt" in vocabulary_json:
        related_reading.jlpt = vocabulary_json["jlpt"]
    else:
        retval += "NO JLPT?"
    if "sentence" in vocabulary_json:
        related_reading.sentence_en = vocabulary_json["sentence"]["en"]
        related_reading.sentence_ja = vocabulary_json["sentence"]["ja"]
    else:
        retval += "NO SENTENCE!?"

    related_reading.save()
    retval += "Finished with reading [{}]! Tags:{},".format(related_reading.id, related_reading.tags.count())
    return retval


def associate_tags(reading, tag):
    print("associating [{}] to reading {}".format(tag, reading.vocabulary.meaning))
    tag_obj, created = Tag.objects.get_or_create(name=tag)
    reading.tags.add(tag_obj)


def create_tokens_for_all_users():
    for user in User.objects.all():
        Token.objects.get_or_create(user=user)


def survey_conglomerated_vocabulary():
    count = 0
    for vocab in Vocabulary.objects.all():
        if has_multiple_kanji(vocab):
            print("Found item with multiple Kanji:[{}]".format(vocab.meaning))
            print("\n".join(reading.kana + ": " + reading.character for reading in vocab.readings.all()))
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
