from __future__ import absolute_import
import logging
from django.contrib.auth.models import User
import requests
from django.db.models import Min

from KW.celery import app as celery_app
from kw_webapp import constants
from kw_webapp.models import UserSpecific, Vocabulary, Profile, Level
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import F
from async_messages import messages
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
        if user and not user.profile.on_vacation:
            review_set = UserSpecific.objects.filter(user=user,
                                                     last_studied__lte=level[0],
                                                     streak=level[1],
                                                     needs_review=False)
        else:
            review_set = UserSpecific.objects.filter(user__profile__on_vacation=False,
                                                     last_studied__lte=level[0],
                                                     streak=level[1],
                                                     needs_review=False)
        if review_set.count() > 0:
            logger.info(
                    "{} has {} reviews for SRS level {}".format((user or "all users"), review_set.count(), level[1]))
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
        return review, created

    except UserSpecific.MultipleObjectsReturned:
        us = UserSpecific.objects.filter(vocabulary=vocab, user=user)
        for u in us:
            logger.error(
                    "during {}'s WK sync, we received multiple UserSpecific objects. Details: {}".format(user.username,
                                                                                                         u))


def build_API_sync_string_for_user(user):
    '''
    Builds a vocabulary api string for the user which includes all relevant levels. Goes back 3 levels from current by default.

    :param user: The user to have their vocab updated
    :return: A fully formed and ready-to-request API string.
    '''
    api_call = "https://www.wanikani.com/api/user/{}/vocabulary/".format(user.profile.api_key)
    # if the user has unlocked recent levels, check for new vocab on them as well.
    for level in user.profile.unlocked_levels_list():
        api_call += str(level) + ","
    return api_call


def build_API_sync_string_for_user_for_levels(user, levels):
    '''
    Given a user, build a vocabulary request string based on their api key, for a particular level.
    :param user: The related user.
    :param level: The level of vocabulary we want to update.
    :return: The fully formatted API string that will provide.
    '''
    level_string = ",".join(str(level) for level in levels) if isinstance(levels, list) else levels
    api_call = "https://www.wanikani.com/api/user/{}/vocabulary/{}".format(user.profile.api_key, level_string)
    return api_call


def lock_level_for_user(requested_level, user):
    reviews = UserSpecific.objects.filter(user=user, vocabulary__reading__level=requested_level).distinct()
    count = reviews.count()
    reviews.delete()
    level = Level.objects.get(profile=user.profile, level=requested_level)
    user.profile.unlocked_levels.remove(level)
    return count


def unlock_all_possible_levels_for_user(user):
    """

    :param user: User to fully unlock.
    :return: The list of levels unlocked, how many vocab were unlocked, how many vocab remain locked (as they are locked in WK)
    """
    level_list = [level for level in range(1, user.profile.level + 1)]
    unlocked, locked = unlock_eligible_vocab_from_levels(user, level_list)
    return level_list, unlocked, locked


@celery_app.task()
def unlock_eligible_vocab_from_levels(user, levels):
    """
    I don't like duplicating code like this, but its for the purpose of reducing API call load on WaniKani. It's a hassle if the user caps out.
    :param user: user to add vocab to.
    :param levels: requested level unlock. This can also be a list.
    :return: unlocked count, locked count
    """

    api_string = build_API_sync_string_for_user_for_levels(user, levels)
    r = requests.get(api_string)
    unlocked, locked = process_vocabulary_response_for_unlock(user, r)
    return unlocked, locked


def get_wanikani_level_by_api_key(api_key):
    api_string = "https://www.wanikani.com/api/user/{}/user-information".format(api_key)
    r = requests.get(api_string)
    if r.status_code == 200:
        json_data = r.json()
        try:
            user_info = json_data["user_information"]
            level = user_info["level"]
            return level
        except KeyError:
            return None
        return


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
        try:
            user_info = json_data["user_information"]
            user.profile.title = user_info["title"]
            user.profile.join_date = datetime.utcfromtimestamp(user_info["creation_date"])
            user.profile.topics_count = user_info["topics_count"]
            user.profile.posts_count = user_info["posts_count"]
            user.profile.about = user_info["about"]
            user.profile.set_website(user_info["website"])
            user.profile.set_twitter_account(user_info["twitter"])
            if user.profile.follow_me:
                user.profile.unlocked_levels.get_or_create(level=user_info["level"])
                if user_info["level"] < user.profile.level: #we have detected a user reset on WK
                    user.profile.handle_wanikani_reset(user_info["level"])
                else:
                    user.profile.level = user_info["level"]


            user.profile.gravatar = user_info["gravatar"]
            user.profile.api_valid = True
            user.profile.last_wanikani_sync_date = timezone.now()
            user.profile.save()

            logger.info("Synced {}'s Profile.".format(user.username))
            return True
        except KeyError as e:
            user.profile.api_valid = False
            user.profile.save()

    else:
        return False


@celery_app.task()
def sync_with_wk(user, full_sync=False):
    '''
    Takes a user. Checks the vocab list from WK for all levels. If anything new has been unlocked on the WK side,
    it also unlocks it here on Kaniwani and creates a new review for the user.

    :param full_sync: if set to True, will sync only user's most recent 3 levels. This is for during login when it is synchronous.
    :param user: The user to check for new unlocks
    :return: None
    '''
    # We split this into two seperate API calls as we do not necessarily know the current level until
    # For the love of god don't delete this next line
    profile_sync_succeeded = sync_user_profile_with_wk(user)
    if user.profile.api_valid:
        if not full_sync:
            new_review_count, new_synonym_count = sync_recent_unlocked_vocab_with_wk(user)
        else:
            new_review_count, new_synonym_count = sync_unlocked_vocab_with_wk(user)

        #Async messaging system.
        if new_review_count or new_synonym_count:
            messages.success(user, "Your Wanikani Profile has been synced. You have {} new reviews, and {} new synonyms".format(new_review_count, new_synonym_count))



        return profile_sync_succeeded, new_review_count, new_synonym_count
    else:
        logger.warn(
                "Not attempting to sync, since API key is invalid, or user has indicated they do not want to be followed ")


def create_new_vocabulary(vocabulary_json):
    '''
    Creates a new vocabulary based on a json object provided by Wanikani and returns this vocabulary.
    :param vocabulary_json: A JSON object representing a single vocabulary, as provided by Wanikani.
    :return: The newly created Vocabulary object.
    '''

    character = vocabulary_json["character"]
    kana_list = [reading.strip() for reading in
                 vocabulary_json["kana"].split(",")]  # Splits out multiple readings for one vocab.
    meaning = vocabulary_json["meaning"]
    level = vocabulary_json["level"]
    vocab = Vocabulary.objects.create(meaning=meaning)
    for reading in kana_list:
        vocab.reading_set.get_or_create(kana=reading, character=character, level=level)
        logger.info("added reading to {}: {} ".format(vocab, reading))

    logger.info("Created new vocabulary with meaning {} and legal readings {}".format(meaning, kana_list))
    return vocab


def associate_readings_to_vocab(vocab, vocabulary_json):
    kana_list = [reading.strip() for reading in
                 vocabulary_json["kana"].split(",")]  # Splits out multiple readings for one vocab.
    character = vocabulary_json["character"]
    level = vocabulary_json["level"]
    for reading in kana_list:
        new_reading, created = vocab.reading_set.get_or_create(kana=reading, character=character, level=level)
        if created:
            logger.info("""Created new reading: {}, level {}
                                     associated to vocab {}""".format(new_reading.kana, new_reading.level,
                                                                      new_reading.vocabulary.meaning))
    return vocab


def get_or_create_vocab_by_json(vocab_json):
    '''
    if lookup by meaning fails, create a new vocab object and return it. See JSON Example here https://www.wanikani.com/api
    :param: vocab_json: a dictionary holding the information needed to create new vocabulary.
    :return:
    '''
    try:
        vocab = get_vocab_by_meaning(vocab_json['meaning'])
    except Vocabulary.DoesNotExist as e:
        vocab = create_new_vocabulary(vocab_json)
    return vocab


def add_synonyms_from_api_call_to_review(review, user_specific_json):
    new_synonym_count = 0
    if user_specific_json["user_synonyms"] is None:
        return review, new_synonym_count

    for synonym in user_specific_json["user_synonyms"]:
        _, created = review.meaningsynonym_set.get_or_create(text=synonym)
        if created:
            new_synonym_count += 1
    return review, new_synonym_count


def associate_synonyms_to_vocab(user, vocab, user_specific):
    review = None
    new_synonym_count = 0

    try:
        review = UserSpecific.objects.get(user=user, vocabulary=vocab)
        _, new_synonym_count = add_synonyms_from_api_call_to_review(review, user_specific)
    except UserSpecific.DoesNotExist:
        pass

    return review, new_synonym_count


def get_users_reviews(user):
    if user.profile.only_review_burned:
        return UserSpecific.objects.filter(user=user, wanikani_burned=True, hidden=False)
    else:
        return UserSpecific.objects.filter(user=user, hidden=False)


def get_users_current_reviews(user):
    if user.profile.only_review_burned:
        return UserSpecific.objects.filter(user=user,
                                           needs_review=True,
                                           wanikani_burned=True,
                                           hidden=False,
                                           burned=False)
    else:
        return UserSpecific.objects.filter(user=user,
                                           needs_review=True,
                                           hidden=False,
                                           burned=False)


def get_users_future_reviews(user, time_limit=None):
    if user.profile.only_review_burned:
        queryset = UserSpecific.objects.filter(user=user,
                                           needs_review=False,
                                           wanikani_burned=True,
                                           hidden=False,
                                           burned=False).annotate(Min('next_review_date')).order_by('next_review_date')
    else:
        queryset = UserSpecific.objects.filter(user=user,
                                           needs_review=False,
                                           hidden=False,
                                           burned=False).annotate(Min('next_review_date')).order_by('next_review_date')

    if isinstance(time_limit, timedelta):
        queryset = queryset.filter(next_review_date__lte=timezone.now() + time_limit)

    return queryset




def process_vocabulary_response_for_unlock(user, response):
    """
    Given a response object from Requests.get(), iterate over the list of vocabulary, and synchronize the user.
    :param user:
    :param response:
    :return:
    """
    r = response
    if r.status_code == 200:
        json_data = r.json()
        vocab_list = json_data['requested_information']
        vocab_list = [vocab_json for vocab_json in vocab_list if
                      vocab_json['user_specific'] is not None]  # filters out locked items.
        unlocked = len(vocab_list)
        locked = len(json_data['requested_information']) - unlocked
        for vocabulary_json in vocab_list:
            user_specific = vocabulary_json['user_specific']
            vocab = get_or_create_vocab_by_json(vocabulary_json)
            vocab = associate_readings_to_vocab(vocab, vocabulary_json)
            new_review, created = associate_vocab_to_user(vocab, user)
            new_review, synonyms_added_count = add_synonyms_from_api_call_to_review(new_review, user_specific)
            new_review.wanikani_srs = user_specific["srs"]
            new_review.wanikani_srs_numeric = user_specific["srs_numeric"]
            new_review.wanikani_burned = user_specific["burned"]
            new_review.save()
        logger.info("Unlocking level for {}".format(user.username))
        return unlocked, locked
    else:
        logger.error("{} COULD NOT Unlock Level. {}}".format(user.username, r.status_code))
        return 0, 0


def process_vocabulary_response_for_user(user, response):
    """
    Given a response object from Requests.get(), iterate over the list of vocabulary, and synchronize the user.
    :param user:
    :param response:
    :return:
    """
    r = response
    new_review_count = 0
    new_synonym_count = 0
    if r.status_code == 200:
        json_data = r.json()
        vocab_list = json_data['requested_information']
        vocab_list = [vocab_json for vocab_json in vocab_list if
                      vocab_json['user_specific'] is not None]  # filters out locked items.
        for vocabulary_json in vocab_list:
            user_specific = vocabulary_json['user_specific']
            vocab = get_or_create_vocab_by_json(vocabulary_json)
            vocab = associate_readings_to_vocab(vocab, vocabulary_json)
            if user.profile.follow_me:
                new_review, created = associate_vocab_to_user(vocab, user)
                if created:
                    new_review_count += 1
                new_review, synonyms_added_count = add_synonyms_from_api_call_to_review(new_review, user_specific)
                new_synonym_count += synonyms_added_count
            else:  # User does not want to be followed, so we prevent creation of new vocab, and sync only synonyms instead.
                new_review, synonyms_added_count = associate_synonyms_to_vocab(user, vocab, user_specific)
                new_synonym_count += synonyms_added_count
            if new_review:
                new_review.wanikani_srs = user_specific["srs"]
                new_review.wanikani_srs_numeric = user_specific["srs_numeric"]
                new_review.wanikani_burned = user_specific["burned"]
                new_review.save()
        logger.info("Synced Vocabulary for {}".format(user.username))
        return new_review_count, new_synonym_count
    else:
        logger.error("{} COULD NOT SYNC WITH WANIKANI. RETURNED STATUS CODE: {}".format(user.username, r.status_code))
        return 0, 0


def sync_recent_unlocked_vocab_with_wk(user):
    if user.profile.unlocked_levels_list():
        levels = [level for level in range(user.profile.level - 2, user.profile.level + 1) if
                  level in user.profile.unlocked_levels_list()]
        if levels:
            request_string = build_API_sync_string_for_user_for_levels(user, levels)
            r = requests.get(request_string)
            new_review_count, new_synonym_count = process_vocabulary_response_for_user(user, r)
            return new_review_count, new_synonym_count
    return 0, 0


def sync_unlocked_vocab_with_wk(user):
    if user.profile.unlocked_levels_list():
        request_string = build_API_sync_string_for_user(user)
        r = requests.get(request_string)
        new_review_count, new_synonym_count = process_vocabulary_response_for_user(user, r)
        return new_review_count, new_synonym_count
    else:
        return 0, 0


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
        sync_with_wk.delay(user, full_sync=True)
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
    url = "https://www.wanikani.com/api/user/" + constants.API_KEY + "/vocabulary/{}"
    logger.info("Staring DB Repopulation from WaniKani")
    for level in range(constants.LEVEL_MIN, constants.LEVEL_MAX + 1):
        r = requests.get(url.format(level))
        if r.status_code == 200:
            json_data = r.json()
            vocabulary_list = json_data['requested_information']
            for vocabulary in vocabulary_list:
                sync_single_vocabulary_item_by_json(vocabulary)
        else:
            logger.error("Status code returned from WaniKani API was not 200! It was {}".format(r.status_code))


def sync_single_vocabulary_item_by_json(vocabulary_json):
    meaning = vocabulary_json["meaning"]
    new_vocab, created = Vocabulary.objects.get_or_create(meaning=meaning)
    associate_readings_to_vocab(new_vocab, vocabulary_json)
    if created:
        logger.info("Found new Vocabulary item from WaniKani:{}".format(new_vocab.meaning))


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
        # TODO dump this before the push.
        review.save()

    return us.count()


def pull_user_synonyms_by_level(user, level):
    '''
    Retrieves vocabulary list from the WK API, specifically searching to pull in synonyms.

    :param user: User to pull WK synonyms or
    :param level: The level for synonyms that should be pulled
    :return: None
    '''
    request_string = build_API_sync_string_for_user_for_levels(user, level)
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
                        for synonym in vocabulary['user_specific']['user_synonyms']:
                            review.meaningsynonym_set.get_or_create(text=synonym)
                        review.save()
                    except UserSpecific.DoesNotExist as e:
                        logger.error("Couldn't pull review during a synonym sync: {}".format(e))
                    except KeyError as e:
                        logger.error("No user_specific or synonyms?: {}".format(json_data))
                    except UserSpecific.MultipleObjectsReturned:
                        reviews = UserSpecific.objects.filter(user=user, vocabulary__meaning=meaning)
                        for review in reviews:
                            logger.error(
                                    "Found something janky! Multiple reviews under 1 vocab meaning?!?: {}".format(
                                            review))
        except KeyError:
            logger.error("NO requested info?: {}".format(json_data))
    else:
        logger.error("Status code returned from WaniKani API was not 200! It was {}".format(r.status_code))


def pull_all_user_synonyms(user=None):
    '''
    Syncs up the user's synonyms for WK for all levels that they have currently unlocked.

    :param user: The user to pull all synonyms for
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


def user_returns_from_vacation(user):
    """
    Called when a user disables vacation mode. A one-time pass through their reviews in order to correct their last_studied_date, and quickly run an SRS run to determine which reviews currently need to be looked at.
    """
    logger.info("{} has returned from vacation!".format(user.username))
    vacation_date = user.profile.vacation_date
    if vacation_date:
        users_reviews = UserSpecific.objects.filter(user=user)
        elapsed_vacation_time = timezone.now() - vacation_date
        logger.info("User {} has been gone for timedelta: {}".format(user.username, str(elapsed_vacation_time)))
        updated_count = users_reviews.update(last_studied=F('last_studied') + elapsed_vacation_time)
        users_reviews.update(next_review_date=F('next_review_date') + elapsed_vacation_time)
        logger.info("brought {} reviews out of hibernation for {}".format(updated_count, user.username))
        all_srs(user)
    user.profile.vacation_date = None
    user.profile.on_vacation = False
    user.profile.save()
