from __future__ import absolute_import
import logging

from celery import shared_task
from django.contrib.auth.models import User
from django.db.models import Min
from kw_webapp.wanikani import make_api_call
from kw_webapp.wanikani import exceptions
from kw_webapp import constants
from kw_webapp.models import UserSpecific, Vocabulary, Profile, Level
from datetime import timedelta, datetime
from django.utils import timezone
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

@shared_task
def all_srs(user=None):
    '''
    Task that performs an SRS update for users. Checks user current streak and last_reviewed_date in order to determine
    when the next review should be. If the time for the review is in the past, flag it for review for the user.

    :param user: Optional Param, the user to be updated. If left blank, will update all users.
    :return: None
    '''
    logger.info("Beginning SRS run for {}.".format(user or "all users"))
    for streak, srs_timing in constants.SRS_TIMES.items():

        study_threshold = past_time(srs_timing)
        if user and not user.profile.on_vacation:
            review_set = UserSpecific.objects.filter(user=user,
                                                     last_studied__lte=study_threshold,
                                                     streak=streak,
                                                     needs_review=False)
        else:
            review_set = UserSpecific.objects.filter(user__profile__on_vacation=False,
                                                     last_studied__lte=study_threshold,
                                                     streak=streak,
                                                     needs_review=False)
        if review_set.count() > 0:
            logger.info(
                "{} has {} reviews for SRS level {}".format((user or "all users"), review_set.count(), streak))
        else:
            logger.info("{} has no reviews for SRS level {}".format((user or "all users"), streak))
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


@shared_task
def unlock_eligible_vocab_from_levels(user, levels):
    """
    I don't like duplicating code like this, but its for the purpose of reducing API call load on WaniKani. It's a hassle if the user caps out.
    :param user: user to add vocab to.
    :param levels: requested level unlock. This can also be a list.
    :return: unlocked count, locked count
    """
    unlocked = locked = 0

    api_call_string = build_API_sync_string_for_user_for_levels(user, levels)

    try:
        response = make_api_call(api_call_string)
        unlocked, locked = process_vocabulary_response_for_unlock(user, response)
    except exceptions.InvalidWaniKaniKey:
        logger.error("Invalid key found for user {}".format(user.username))
        user.profile.api_valid = False
        user.profile.save()
    except exceptions.WanikaniAPIException:
        logger.error("Non-invalid key error found during API call. ")
    return unlocked, locked


def get_wanikani_level_by_api_key(api_key):
    api_string = "https://www.wanikani.com/api/user/{}/user-information".format(api_key)
    response = make_api_call(api_string)
    user_info = response["user_information"]
    level = user_info["level"]
    return level


@shared_task
def sync_user_profile_with_wk(user):
    '''
    Hits the WK api with user information in order to synchronize user metadata such as level and gravatar information.

    :param user: The user to sync their profile with WK.
    :return: boolean indicating the success of the API call.
    '''
    api_string = "https://www.wanikani.com/api/user/{}/user-information".format(user.profile.api_key)

    try:
        json_data = make_api_call(api_string)
    except exceptions.InvalidWaniKaniKey:
        user.profile.api_valid = False;
        user.profile.save()
        return False

    user_info = json_data["user_information"]
    user.profile.title = user_info["title"]
    user.profile.join_date = datetime.utcfromtimestamp(user_info["creation_date"])
    user.profile.topics_count = user_info["topics_count"]
    user.profile.posts_count = user_info["posts_count"]
    user.profile.about = user_info["about"]
    user.profile.set_website(user_info["website"])
    user.profile.set_twitter_account(user_info["twitter"])
    user.profile.gravatar = user_info["gravatar"]
    user.profile.last_wanikani_sync_date = timezone.now()
    user.profile.api_valid = True
    if user.profile.follow_me:
        user.profile.unlocked_levels.get_or_create(level=user_info["level"])
        user.profile.handle_wanikani_level_change(user_info["level"])

    user.profile.save()

    logger.info("Synced {}'s Profile.".format(user.username))
    return True


@shared_task
def sync_with_wk(user_id, full_sync=False):
    '''
    Takes a user. Checks the vocab list from WK for all levels. If anything new has been unlocked on the WK side,
    it also unlocks it here on Kaniwani and creates a new review for the user.

    :param user_id: id of the user to sync
    :param full_sync:
    :return: None
    '''
    # We split this into two seperate API calls as we do not necessarily know the current level until
    # For the love of god don't delete this next line
    user = User.objects.get(pk=user_id)
    logger.info("About to begin sync for user {}.".format(user.username))
    profile_sync_succeeded = sync_user_profile_with_wk(user)
    if user.profile.api_valid:
        if not full_sync:
            new_review_count, new_synonym_count = sync_recent_unlocked_vocab_with_wk(user)
        else:
            new_review_count, new_synonym_count = sync_unlocked_vocab_with_wk(user)

        # Async messaging system.
        if new_review_count or new_synonym_count:
            logger.info("Sending message to front-end for user {}".format(user.username))
            messages.success(user,
                             "Your Wanikani Profile has been synced. You have {} new reviews, and {} new synonyms".format(
                                 new_review_count, new_synonym_count))

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
    kana_list = [reading.strip() for reading in
                 vocabulary_json["kana"].split(",")]  # Splits out multiple readings for one vocab.
    meaning = vocabulary_json["meaning"]
    vocab = Vocabulary.objects.create(meaning=meaning)
    vocab = associate_readings_to_vocab(vocab, vocabulary_json)
    logger.info("Created new vocabulary with meaning {} and legal readings {}".format(meaning, kana_list))
    return vocab


def associate_readings_to_vocab(vocab, vocabulary_json):
    kana_list = [reading.strip() for reading in
                 vocabulary_json["kana"].split(",")]  # Splits out multiple readings for one vocab.
    character = vocabulary_json["character"]
    level = vocabulary_json["level"]
    for reading in kana_list:
        new_reading, created = vocab.reading_set.get_or_create(kana=reading, character=character)
        new_reading.level = level
        new_reading.save()
        if created:
            logger.info("""Created new reading: {}, level {}
                                     associated to vocab {}""".format(new_reading.kana, new_reading.level,
                                                                      new_reading.vocabulary.meaning))
    return vocab


def get_or_create_vocab_by_json(vocab_json):
    """
    if lookup by meaning fails, create a new vocab object and return it. See JSON Example here https://www.wanikani.com/api
    :param: vocab_json: a dictionary holding the information needed to create new vocabulary.
    :return:
    """
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
                                               burned=False).annotate(Min('next_review_date')).order_by(
            'next_review_date')
    else:
        queryset = UserSpecific.objects.filter(user=user,
                                               needs_review=False,
                                               hidden=False,
                                               burned=False).annotate(Min('next_review_date')).order_by(
            'next_review_date')

    if isinstance(time_limit, timedelta):
        queryset = queryset.filter(next_review_date__lte=timezone.now() + time_limit)

    return queryset


def process_vocabulary_response_for_unlock(user, json_data):
    """
    Given a JSON Object from WK, iterate over the list of vocabulary, and synchronize the user.
    :param user:
    :param json_data:
    :return:
    """
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


def process_vocabulary_response_for_user(user, json_data):
    """
    Given a response object from Requests.get(), iterate over the list of vocabulary, and synchronize the user.
    :param json_data:
    :param user:
    :return:
    """
    new_review_count = 0
    new_synonym_count = 0
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


def sync_recent_unlocked_vocab_with_wk(user):
    if user.profile.unlocked_levels_list():
        levels = [level for level in range(user.profile.level - 2, user.profile.level + 1) if
                  level in user.profile.unlocked_levels_list()]
        if levels:
            request_string = build_API_sync_string_for_user_for_levels(user, levels)
            json_data = make_api_call(request_string)
            new_review_count, new_synonym_count = process_vocabulary_response_for_user(user, json_data)
            return new_review_count, new_synonym_count
    return 0, 0


def sync_unlocked_vocab_with_wk(user):
    if user.profile.unlocked_levels_list():
        request_string = build_API_sync_string_for_user(user)
        logger.info("Creating sync string for user {}: {}".format(user.username, user.profile.api_key))
        response = make_api_call(request_string)
        new_review_count, new_synonym_count = process_vocabulary_response_for_user(user, response)
        return new_review_count, new_synonym_count
    else:
        return 0, 0


@shared_task
def sync_all_users_to_wk():
    '''
    calls sync_with_wk for all users, causing all users to have their newly unlocked vocabulary synchronized to KW.

    :return: the number of users successfully synced to WK.
    '''
    one_week_ago = past_time(24 * 7)
    logger.info("Beginning Bi-daily Sync for all user!")
    users = User.objects.all().exclude(profile__isnull=True)
    logger.info("Original sync would have occurred for {} users.".format(users.count()))
    users = User.objects.filter(profile__last_visit__gte=one_week_ago)
    logger.info("Sync will occur for {} users.".format(users.count()))
    affected_count = 0
    for user in users:
        print(user.username + " --- " + str(user.profile.last_visit) + " --- " + str(one_week_ago))
        sync_with_wk.delay(user.id, full_sync=True)
        affected_count += 1
    return affected_count


@shared_task
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
        json_data = make_api_call(url.format(level))
        vocabulary_list = json_data['requested_information']
        for vocabulary in vocabulary_list:
            sync_single_vocabulary_item_by_json(vocabulary)


def sync_single_vocabulary_item_by_json(vocabulary_json):
    meaning = vocabulary_json["meaning"]
    new_vocab, created = Vocabulary.objects.get_or_create(meaning=meaning)
    associate_readings_to_vocab(new_vocab, vocabulary_json)
    if created:
        logger.info("Found new Vocabulary item from WaniKani:{}".format(new_vocab.meaning))


def pull_user_synonyms_by_level(user, level):
    '''
    Retrieves vocabulary list from the WK API, specifically searching to pull in synonyms.

    :param user: User to pull WK synonyms or
    :param level: The level for synonyms that should be pulled
    :return: None
    '''
    request_string = build_API_sync_string_for_user_for_levels(user, level)
    json_data = make_api_call(request_string)
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

        # TODO This is an ultra temporary hack until I figure out F() expressions in 1.9
        for rev in users_reviews:
            lst = rev.last_studied
            nsd = rev.next_review_date
            rev.last_studied = lst + elapsed_vacation_time
            rev.next_review_date = nsd + elapsed_vacation_time
            rev.save()

            # updated_count = users_reviews.update(last_studied=F('last_studied') + elapsed_vacation_time)
            # users_reviews.update(next_review_date=F('next_review_date') + elapsed_vacation_time)
            # logger.info("brought {} reviews out of hibernation for {}".format(updated_count, user.username))

    user.profile.vacation_date = None
    user.profile.on_vacation = False
    user.profile.save()
    all_srs(user)
