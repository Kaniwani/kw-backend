import random

import requests
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token

from kw_webapp.models import UserSpecific, Profile, Reading, Tag
from kw_webapp import constants
from kw_webapp.tasks import unlock_eligible_vocab_from_levels
from kw_webapp.tests.utils import create_userspecific, create_review_for_specific_time


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


def create_various_future_reviews_for_user(user):
    now = timezone.now()
    for i in range(0,24):
        for j in range(0,20):
            review = create_review_for_specific_time(user, str(i) + "-" + str(j), now+timezone.timedelta(hours=i))

            review.streak = random.randint(1,8)
            review.save()
            review.refresh_from_db()
            print(review)
