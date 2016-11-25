import requests
from django.utils import timezone

from kw_webapp import constants
from kw_webapp.models import UserSpecific, Profile, Reading, Partial, Tag
from kw_webapp.tasks import unlock_eligible_vocab_from_levels


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


def unlock_level_for_user(level, user):
    unlock_eligible_vocab_from_levels(user, level)


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


def one_time_import_jisho(json_file_path):
    import json
    with open(json_file_path) as file:
        parsed_json = json.load(file)

        for vocabulary_json in parsed_json:
            try:
                related_reading = Reading.objects.get(character=vocabulary_json["ja"]["characters"])
                doTheThing(related_reading, vocabulary_json)
            except Reading.DoesNotExist:
                pass
            except Reading.MultipleObjectsReturned:
                readings = Reading.objects.filter(character=vocabulary_json["ja"]["characters"])
                print("FOUND MULTIPLE READINGS")
                for reading in readings:
                    print(reading.vocabulary.meaning, reading.character, reading.kana, reading.level)
                    doTheThing(reading, vocabulary_json)


def doTheThing(related_reading, vocabulary_json):
    try:
        print("Workin on related reading... {}".format(related_reading.id))
        partials_json = vocabulary_json["partials"]
        [associate_partials(related_reading, partial_json) for partial_json in partials_json]

        tags_json = vocabulary_json['tags']
        [associate_tags(related_reading, tag_json) for tag_json in tags_json]

        related_reading.common = vocabulary_json["common"]
        related_reading.jlpt = vocabulary_json["jlpt"]
        related_reading.sentence_en = vocabulary_json["sentence"]["en"]
        related_reading.sentence_ja = vocabulary_json["sentence"]["ja"]

        related_reading.save()
        print(
            "Finished with reading [{}]! Tags:{}, Partials:{}".format(related_reading.id, related_reading.tags.count(),
                                                                      related_reading.partials.count()))
    except KeyError:
        print(vocabulary_json)


def associate_tags(reading, tag):
    print("associating [{}] to reading {}".format(tag, reading.vocabulary.meaning))
    tag_obj, created = Tag.objects.get_or_create(name=tag)
    reading.tags.add(tag_obj)


def associate_partials(reading, partial_json):
    print("associating Partial [{}] to reading {}".format(partial_json['character'], reading.vocabulary.meaning))
    partial, created = Partial.objects.get_or_create(character=partial_json['character'])
    if created:
        partial.kana = partial_json["reading"]
        partial.meaning = partial_json["meaning"]
        partial.save()

    reading.partials.add(partial)


