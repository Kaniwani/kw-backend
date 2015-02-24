from __future__ import absolute_import
import logging
from django.contrib.auth.models import User
import requests
from KW.celery import app as celery_app
from kw_webapp import constants
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


@celery_app.task()
def all_srs(user=None):
    '''
    Task that performs an SRS update for users. Checks user current streak and last_reviewed_date in order to determine
    when the next review should be. If the time for the review is in the past, flag it for review for the user.

    :param user: Optional Param, the user to be updated. If left blank, will update all users.
    :return: None
    '''
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
    Searches for a vocabulary object based on its meaning.

    :param meaning: meaning to search for
    :return: the vocabulary object, or None
    """
    try:
        v = Vocabulary.objects.get(meaning=meaning)
    except Vocabulary.DoesNotExist:
        logger.error("While attempting to get vocabulary {} we could not find it!".format(meaning))
        raise Vocabulary.DoesNotExist("Couldn't find meaning: {}".format(meaning))
    else:
        return v


def associate_vocab_to_user(vocab, user):
    '''
    takes a vocab, and creates a UserSpecific object for the user based on it. Returns the vocab object.
    :param vocab: the vocabulary object to associate to the user.
    :param user: The user.
    :return: the vocabulary object after association to the user
    '''
    try:
        review, created = UserSpecific.objects.get_or_create(vocabulary=vocab, user=user)
        if created:
            review.needs_review = True
            review.next_review_date = timezone.now()
            review.save()
        return review

    except UserSpecific.MultipleObjectsReturned:
        us = UserSpecific.objects.filter(vocabulary=vocab, user=user)
        for u in us:
            logger.error("during {}'s WK sync, we received multiple UserSpecific objects. Details: {}".format(u))

def build_API_sync_string_for_user(user):
    '''
    Builds a vocabulary api string for the user which includes all relevant levels.

    :param user: The user to have their vocab updated
    :return: A fully formed and ready-to-request API string.
    '''
    api_call = "https://www.wanikani.com/api/user/{}/vocabulary/".format(user.profile.api_key)
    #if the user has unlocked recent levels, check for new vocab on them as well. In our case its within the last 3 levels.
    for level in user.profile.unlocked_levels_list():
        if user.profile.level - level[0] <= 3: #example if i'm 25, and i've set 22 and 23, it will check those as well. But not 21.
            api_call += str(level[0]) + ","
    return api_call

def build_API_sync_string_for_user_for_level(user, level):
    '''
    Given a user, build a vocabulary request string based on their api key, for a particular level.
    :param user: The related user.
    :param level: The level of vocabulary we want to update.
    :return: The fully formatted API string that will provide.
    '''

    api_call = "https://www.wanikani.com/api/user/{}/vocabulary/{}".format(user.profile.api_key, level[0])
    return api_call

@celery_app.task()
def unlock_eligible_vocab_from_level(user, level):
    """
    I don't like duplicating code like this, but its for the purpose of reducing API call load on WaniKani. It's a hassle if the user caps out.
    :param user: user to add vocab to.
    :param level: requested level unlock.
    :return: unlocked count, locked count
    """
    api_string = "https://www.wanikani.com/api/user/{}/vocabulary/{}".format(user.profile.api_key, level)
    r = requests.get(api_string)
    if r.status_code == 200:
        #parsing out the JSON data
        json_data = r.json()
        vocab_info = json_data['requested_information']
        unlocked = locked = 0

        for vocabulary in vocab_info: #go through All vocab for the level
            if vocabulary['user_specific'] is not None: #if user has unlocked it in WK
                vocab = get_vocab_by_meaning(vocabulary['meaning'])
                if vocab:
                    unlocked += 1
                    associate_vocab_to_user(vocab, user) #gets or creates a review object. if created, set it to need review now.
            else:
                locked += 1
        return unlocked, locked

@celery_app.task()
def sync_user_profile_with_wk(user):
    '''
    Hits the WK api with user information in order to synchronize user metadata such as level and gravatar information.

    :param user: The user to sync their profile with WK.
    :return: boolean indicating the success of the API call.
    '''
    api_string = "https://www.wanikani.com/api/user/{}/user-information".format(user.profile.api_key)
    r = requests.get(api_string)
    if r.status_code == 200:
        json_data = r.json()
        user_info = json_data["user_information"]
        user.profile.level = user_info["level"]
        user.profile.unlocked_levels.get_or_create(level=user_info["level"])
        user.profile.gravatar = user_info["gravatar"]
        user.profile.save()
        logger.info("Synced {}'s Profile.".format(user.username))
        return True
    else:
        return False


@celery_app.task()
def sync_with_wk(user):
    '''
    Takes a user. Checks the vocab list from WK for the last 3 levels. If anything new has been unlocked on the WK side,
    it also unlocks it here on Kaniwani and creates a new review for the user.

    :param user: The user to check for new unlocks
    :return: None
    '''
    #We split this into two seperate API calls as we do not necessarily know the current level until
    #For the love of god don't delete this next line
    sync_user_profile_with_wk(user)
    request_string = build_API_sync_string_for_user(user)
    r = requests.get(request_string)
    if r.status_code == 200:
        #parsing out the JSON data
        json_data = r.json()
        vocab_info = json_data['requested_information']

        for vocabulary_json in vocab_info:
            user_specific = vocabulary_json['user_specific']
            if user_specific is not None: #if user has unlocked it in WK
                try:
                    vocab = get_vocab_by_meaning(vocabulary_json['meaning'])
                except Vocabulary.DoesNotExist as e:
                    logger.error(e)
                    vocab = create_new_vocabulary(vocabulary_json)

                new_review = associate_vocab_to_user(vocab, user)

                #Pull user synonyms if any
                #TODO review code for this section before 0.2
                if user_specific["user_synonyms"] is not None:
                    new_review.synonyms = ", ".join([synonym for synonym in user_specific["user_synonyms"]])
                    new_review.save()

        #logger.info("{} recently unlocked: {}".format(user.username, recently_unlocked))
        logger.info("Synced Vocabulary for {}".format(user.username))
    else:
        logger.error("{} COULD NOT SYNC WITH WANIKANI. RETURNED STATUS CODE: {}".format(user.username, r.status_code))

def create_new_vocabulary(vocabulary_json):
    '''
    Creates a new vocabulary based on a json object provided by Wanikani and returns this vocabulary.
    :param vocabulary_json: A JSON object representing a single vocabulary, as provided by Wanikani.
    :return: The newly created Vocabulary object.
    '''

    character = vocabulary_json["character"]
    kana_list = [reading.strip() for reading in vocabulary_json["kana"].split(",")]#Splits out multiple readings for one vocab.
    meaning = vocabulary_json["meaning"]
    level = vocabulary_json["level"]
    vocab = Vocabulary.objects.create(meaning=meaning)
    for reading in kana_list:
        vocab.reading_set.get_or_create(kana=reading, character=character, level=level)
        logger.info("added reading to {}: {} ".format(vocab, reading))

    logger.info("Created new vocabulary with meaning {} and legal readings {}".format(meaning, kana_list))
    return vocab


@celery_app.task()
def sync_all_users_to_wk():
    '''
    calls sync_with_wk for all users, causing all users to have their newly unlocked vocabulary synchronized to KW.

    :return: the number of users successfully synced to WK.
    '''
    logger.info("Beginning Bi-daily Sync for all user!")
    users = User.objects.all().exclude(profile__isnull=True)
    affected_count = 0
    for user in users:
        sync_with_wk.delay(user)
        affected_count += 1
    return affected_count

@celery_app.task()
def repopulate():
    '''
    A task that uses my personal API key in order to re-sync the database. Koichi often decides to switch things around
    on a level-per-level basis, or add synonyms, or change which readings are allowed. This method attempts to synchronize
    our data sets.

    :return:
    '''
    url = "https://www.wanikani.com/api/user/50f4abec6b4afdecdb892938e1193edb/vocabulary/{}"
    logger.info("Staring DB Repopulation from WaniKani")
    for level in range(1, 51):
        r = requests.get(
            url.format(level))
        if r.status_code == 200:
            json_data = r.json()
            vocabulary_list = json_data['requested_information']
            for vocabulary in vocabulary_list:
                character = vocabulary["character"]
                kana = [reading.strip() for reading in vocabulary["kana"].split(",")]#Splits out multiple readings for one vocab.
                meaning = vocabulary["meaning"]
                level = vocabulary["level"]
                new_vocab, created = Vocabulary.objects.get_or_create(
                    meaning=meaning)
                if created:
                    logger.info("Found new Vocabulary item from WaniKani:{}".format(new_vocab.meaning))
                for reading in kana:
                    new_reading, created = new_vocab.reading_set.get_or_create(
                        kana=reading, character=character, level=level)
                    if created:
                        logger.info("""Created new reading: {}, level {}
                                     associated to vocab {}""".format(new_reading.kana,new_reading.level, new_reading.vocabulary.meaning))
        else:
            logger.error("Status code returned from WaniKani API was not 200! It was {}".format(r.status_code))

def correct_next_review_times():
    '''
    This is a one-time function that will need to be called when update 0.2 is pushed.
    Seeing as we are adding a new field, ,which gets automatically calculated upon new reviews,
    we must execute a one-time fix for all extant reviews.

    :return: The number of affected reviews
    '''


    us = UserSpecific.objects.filter(next_review_date=None, streak__lte=8)
    for review in us:
        review.next_review_date = review.last_studied + timedelta(hours=constants.SRS_TIMES[review.streak])
        #TODO dump this before the push.
        review.save()

    return us.count()


def pull_user_synonyms_by_level(user, level):
    '''
    Retrieves vocabulary list from the WK API, specifically searching to pull in synonyms.

    :param user: User to pull WK synonyms or
    :param level: The level for synonyms that should be pulled
    :return: None
    '''
    request_string = build_API_sync_string_for_user_for_level(user, level)
    r = requests.get(request_string)
    if r.status_code == 200:
        json_data = r.json()
        try: 
            vocabulary_list = json_data['requested_information']
            for vocabulary in vocabulary_list:
                meaning = vocabulary["meaning"]
                if vocabulary['user_specific'] and vocabulary['user_specific']['user_synonyms']:
                    try:
                        review = UserSpecific.objects.get(user=user, vocabulary__meaning=meaning)
                        review.synonyms = vocabulary['user_specific']['user_synonyms']
                        review.save()
                    except UserSpecific.DoesNotExist as e:
                        logger.error("Couldn't pull review during a synonym sync: {}".format(e))
                    except KeyError as e:
                        logger.error("No user_specific or synonyms?: {}".format(json_data))
                    except UserSpecific.MultipleObjectsReturned:
                        reviews = UserSpecific.objects.filter(user=user, vocabulary__meaning=meaning)
                        for review in reviews:
                            logger.error("Found something janky! Multiple reviews under 1 vocab meaning?!?: {}".format(review))
        except KeyError:
            logger.error("NO requested info?: {}".format(json_data))
    else:
        logger.error("Status code returned from WaniKani API was not 200! It was {}".format(r.status_code))


def pull_all_user_synonyms(user = None):
    '''
    Syncs up the user's synonyms for WK for all levels that they have currently unlocked.

    :param user: The user to pull all synonys for
    :return: None
    '''
    if user:
        for level in user.profile.unlocked_levels_list():
            pull_user_synonyms_by_level(user, level)
            logger.info("Pulled user synonyms for {}".format(user.username))
    else:
        for profile in Profile.objects.all():
            if len(profile.api_key) == 32:
                user = profile.user
                for level in profile.unlocked_levels_list():
                    pull_user_synonyms_by_level(user, level)
                logger.info("Pulled user synonyms for {}".format(user.username))



