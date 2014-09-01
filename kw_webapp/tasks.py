from __future__ import absolute_import
import logging
from django.contrib.auth.models import User
import requests
from KW.celery import app as celery_app
from kw_webapp.models import UserSpecific, Vocabulary, Profile
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger('kw.tasks')


def past_time(hours_ago):
    """
    Generates a datetime object X hours in the past.
    :param hours_ago: number of hours ago you'd like a datetime for
    :return: a datetime object indicting the time it was hours_ago hours ago.
    """
    srs_level_hours = timedelta(hours=hours_ago)
    now = timezone.now()
    return now - srs_level_hours


def update_from_wk_profile(user, user_info):
        logger.info("Updating {}'s profile information. ")
        user.profile.level = user_info["level"]
        user.profile.unlocked_levels.get_or_create(level=user_info["level"])
        user.profile.gravatar = user_info["gravatar"]
        user.profile.save()
        logger.info(" finished Syncing {}'s profile data from WK.".format(user.username))



@celery_app.task()
def all_srs(user=None):
    logger.info("Beginning SRS run for {}.".format(user or "all users"))
    hours = [4, 4, 8, 24, 72, 168, 336, 720, 2160]
    srs_level = zip(map(lambda x: past_time(x), hours), range(0, 9))
    for level in srs_level:
        if user:
            review_set = UserSpecific.objects.filter(user=user,
                                                     last_studied__lte=level[0],
                                                     streak=level[1],
                                                     needs_review=False)
        else:
            review_set = UserSpecific.objects.filter(last_studied__lte=level[0],
                                                     streak=level[1],
                                                     needs_review=False)
        if review_set.count() > 0:
            logger.info("{} has {} reviews for SRS level {}".format((user or "all users"), review_set.count(), level[1]))
        else:
            logger.info("{} has no reviews for SRS level {}".format((user or "all users"), level[1]))
        review_set.update(needs_review=True)
    logger.info("Finished SRS run for {}.".format(user or "all users"))


def get_vocab_by_meaning(meaning):
    """

    :param meaning: meaning to search for
    :return: the vocabulary object, or None
    """
    try:
        v = Vocabulary.objects.get(meaning=meaning)
    except Vocabulary.DoesNotExist:
        logger.error("While attempting to get vocabulary {} we could not find it!".format(meaning))
        return None
    else:
        return v


def associate_vocab_to_user(vocab, user):
    try:
        review, created = UserSpecific.objects.get_or_create(vocabulary=vocab, user=user)
        if created:
            logger.info("{} just unlocked {} from WK.".format(user.username, review.vocabulary.meaning))
            review.needs_review = True
            review.save()
    except UserSpecific.MultipleObjectsReturned:
        us = UserSpecific.objects.filter(vocabulary=vocab, user=user)
        for u in us:
            logger.error("during {}'s WK sync, we received multiple UserSpecific objects. Details: {}".format(u))

def build_API_sync_string_for_user(user):
    api_call = "https://www.wanikani.com/api/user/{}/vocabulary/".format(user.profile.api_key)
    #if the user has unlocked recent levels, check for new vocab on them as well. In our case its within the last 3 levels.
    for level in user.profile.unlocked_levels_list():
        if user.profile.level - level[0] <= 3: #example if i'm 25, and i've set 22 and 23, it will check those as well. But not 21.
            api_call += str(level[0]) + ","
    logger.info("API call being made: {}".format(api_call))
    return api_call


@celery_app.task()
def sync_with_wk(user):
    logger.info("Beginning Sync with WK for {}".format(user.username))
    request_string = build_API_sync_string_for_user(user)
    r = requests.get(request_string)
    if r.status_code == 200:
        #parsing out the JSON data
        json_data = r.json()
        user_info = json_data["user_information"]
        vocab_info = json_data['requested_information']

        #update basic user information
        update_from_wk_profile(user, user_info)

        for vocabulary in vocab_info: #go through All vocab for the level
            if vocabulary['user_specific'] is not None: #if user has unlocked it in WK
                vocab = get_vocab_by_meaning(vocabulary['meaning'])
                if vocab:
                    associate_vocab_to_user(vocab, user) #gets or creates a review object. if created, set it to need review now.

@celery_app.task()
def sync_all_users_to_wk():
    logger.info("Beginning Daily Sync for all user!")
    users = User.objects.all()
    for user in users:
        try:
            print(user.profile.level)
            sync_with_wk.delay(user)
        except Profile.DoesNotExist:
            logger.error("{} has no profile!".format(user.username))