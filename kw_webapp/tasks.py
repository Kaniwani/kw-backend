from __future__ import absolute_import

from collections import OrderedDict

from celery import shared_task, task
from django.contrib.auth.models import User
from django.db.models import F, Count
from django.db.models import Min
from django.db.models.functions import TruncHour, TruncDate

from kw_webapp.constants import WANIKANI_SRS_LEVELS, KANIWANI_SRS_LEVELS, KwSrsLevel
from kw_webapp.wanikani import make_api_call
from kw_webapp.wanikani import exceptions
from kw_webapp import constants
from kw_webapp.models import MeaningReview, Vocabulary, Profile, Level, MeaningSynonym, AnswerSynonym
from datetime import timedelta, datetime
from django.utils import timezone

import logging
logger = logging.getLogger(__name__)


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
    logger.info("Beginning  SRS run for {}.".format(user or "all users"))
    affected_count = 0
    now = timezone.now()
    slightly_ahead_of_now = now + timedelta(minutes=1)

    # Fetches all reviews with next_review_date greater than or equal to NOW, flips them all to needs_review=True
    if user and user.profile.on_vacation:
        logger.info("Skipping SRS for user {} as they are on vacation as of {}".format(user.username, user.profile.vacation_date))
        return 0

    if user:
            review_set = MeaningReview.objects.filter(user=user,
                                                      next_review_date__lte=slightly_ahead_of_now,
                                                      needs_review=False)
    else:
        review_set = MeaningReview.objects.filter(user__profile__on_vacation=False,
                                                  next_review_date__lte=slightly_ahead_of_now,
                                                  needs_review=False)

    affected_count += review_set.update(needs_review=True)
    logger.info("User {} has {} new reviews.".format(user.username if user else "all users", affected_count))
    return affected_count


def get_vocab_by_kanji(kanji):
    v = Vocabulary.objects.filter(readings__character=kanji).distinct()
    number_of_vocabulary = v.count()
    if number_of_vocabulary > 1:
        error = "Found multiple Vocabulary with identical kanji with ids: [{}]".format(", ".join([str(vocab.id) for vocab in v]))
        logger.error(error)
        raise Vocabulary.MultipleObjectsReturned(error)
    elif number_of_vocabulary == 0:
        logger.error("While attempting to get vocabulary {} we could not find it!".format(kanji))
        raise Vocabulary.DoesNotExist("Couldn't find meaning: {}".format(kanji))
    else:
        return v.first()


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
        review, created = MeaningReview.objects.get_or_create(vocabulary=vocab, user=user)
        if created:
            review.needs_review = True
            review.next_review_date = timezone.now()
            review.save()
        return review, created

    except MeaningReview.MultipleObjectsReturned:
        us = MeaningReview.objects.filter(vocabulary=vocab, user=user)
        for u in us:
            logger.error(
                "during {}'s WK sync, we received multiple UserSpecific objects. Details: {}".format(user.username,
                                                                                                     u))
        return None, None


def get_level_pages(levels):
    page_size = 5
    return [levels[i:i+page_size] for i in range(0, len(levels), page_size)]


def build_API_sync_string_for_user(user):
    '''
    Builds a vocabulary api string for the user which includes all relevant levels. Goes back 3 levels from current by default.

    :param user: The user to have their vocab updated
    :return: A fully formed and ready-to-request API string.
    '''
    api_call = "https://www.wanikani.com/api/user/{}/vocabulary/".format(user.profile.api_key)
    # if the user has unlocked recent levels, check for new vocab on them as well.
    levels = user.profile.unlocked_levels_list()
    level_string = ",".join(str(level) for level in levels) if isinstance(levels, list) else levels
    api_call += level_string
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
    api_call += ','
    return api_call


def lock_level_for_user(requested_level, user):
    requested_level = int(requested_level)
    reviews = MeaningReview.objects.filter(user=user, vocabulary__readings__level=requested_level).distinct()
    count = reviews.count()
    reviews.delete()
    level = Level.objects.get(profile=user.profile, level=requested_level)
    user.profile.unlocked_levels.remove(level)
    level.delete()
    return count


def unlock_all_possible_levels_for_user(user):
    """

    :param user: User to fully unlock. :return: The list of levels unlocked, how many vocab were unlocked,
    how many vocab remain locked (as they are locked in WK)
    """
    level_list = [level for level in range(1, user.profile.level + 1)]
    unlocked_now, unlocked_total, locked = unlock_eligible_vocab_from_levels(user, level_list)
    return level_list, unlocked_now, unlocked_total, locked


@shared_task
def unlock_eligible_vocab_from_levels(user, levels):
    """
    I don't like duplicating code like this, but its for the purpose of reducing API call load on WaniKani. It's a
    hassle if the user caps out.
    :param user: user to add vocab to. :param levels: requested level unlock. This can
    also be a list. :return: unlocked count, locked count
    """

    api_call_string = build_API_sync_string_for_user_for_levels(user, levels)

    try:
        response = make_api_call(api_call_string)
        unlocked_this_request, total_unlocked, locked = process_vocabulary_response_for_unlock(user, response)
        return unlocked_this_request, total_unlocked, locked
    except exceptions.InvalidWaniKaniKey:
        logger.error("Invalid key found for user {}".format(user.username))
        user.profile.api_valid = False
        user.profile.save()
    except exceptions.WanikaniAPIException as e:
        logger.error("Non-invalid key error found during API call. ", e)


def get_wanikani_level_by_api_key(api_key):
    api_string = "https://www.wanikani.com/api/user/{}/user-information".format(api_key)
    response = make_api_call(api_string)
    user_info = response["user_information"]
    level = user_info["level"]
    return level


def build_user_information_api_string(api_key):
    return "https://www.wanikani.com/api/user/{}/user-information".format(api_key)


@shared_task
def sync_user_profile_with_wk(user):
    '''
    Hits the WK api with user information in order to synchronize user metadata such as level and gravatar information.

    :param user: The user to sync their profile with WK.
    :return: boolean indicating the success of the API call.
    '''
    api_string = build_user_information_api_string(user.profile.api_key)

    try:
        json_data = make_api_call(api_string)
    except exceptions.InvalidWaniKaniKey:
        user.profile.api_valid = False
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
    if profile_sync_succeeded:
        if not full_sync:
            new_review_count, new_synonym_count = sync_recent_unlocked_vocab_with_wk(user)
        else:
            new_review_count, new_synonym_count = sync_unlocked_vocab_with_wk(user)

        return profile_sync_succeeded, new_review_count, new_synonym_count
    else:
        logger.warning(
            "Not attempting to sync, since API key is invalid, or user has indicated they do not want to be followed ")
        return profile_sync_succeeded, 0, 0


def create_new_vocabulary(vocabulary_json):
    '''
    Creates a new vocabulary based on a json object provided by Wanikani and returns this vocabulary.
    :param vocabulary_json: A JSON object representing a single vocabulary, as provided by Wanikani.
    :return: The newly created Vocabulary object.
    '''
    meaning = vocabulary_json["meaning"]
    vocab = Vocabulary.objects.create(meaning=meaning, source=constants.Source.WANIKANI)
    vocab = update_local_vocabulary_information(vocab, vocabulary_json)
    return vocab


def update_local_vocabulary_information(vocab, vocabulary_json):

    kana_list = [reading.strip() for reading in vocabulary_json["kana"].split(",")]
    # Update the local meaning based on WK meaning
    meaning = vocabulary_json['meaning']
    vocab.meaning = meaning

    character = vocabulary_json["character"]
    level = vocabulary_json["level"]
    for reading in kana_list:
        new_reading, created = vocab.readings.get_or_create(kana=reading, character=character)
        new_reading.level = level
        new_reading.save()
        if created:
            logger.info("""Created new reading: {}, level {}
                                     associated to vocab {}""".format(new_reading.kana, new_reading.level,
                                                                      new_reading.vocabulary.meaning))
    vocab.save()
    return vocab


def get_or_create_vocab_by_json(vocab_json):
    """
    if lookup by meaning fails, create a new vocab object and return it. See JSON Example here
    https://www.wanikani.com/api
    :param: vocab_json: a dictionary holding the information needed to create new
    vocabulary.
    :return: vocabulary object.
    """

    try:
        vocab = get_vocab_by_kanji(vocab_json['character'])
        created = False
    except Vocabulary.DoesNotExist:
        vocab = create_new_vocabulary(vocab_json)
        created = True
    return vocab, created


def has_multiple_kanji(vocab):
    kanji = [reading.character for reading in vocab.readings.all()]
    kanji2 = set(kanji)
    return len(kanji2) > 1


def synchronize_synonyms(review, user_specific_json):
    synonym_count = 0
    incoming_synonyms = user_specific_json["user_synonyms"]
    if incoming_synonyms is None or len(incoming_synonyms) == 0:
        return review, synonym_count

    # Add new synonyms
    for synonym in incoming_synonyms:
        _, created = review.meaning_synonyms.get_or_create(text=synonym)
        if created:
            synonym_count += 1

    # Delete Stale Synonyms
    for synonym in review.meaning_synonyms.all():
        if synonym.text not in user_specific_json["user_synonyms"]:
            synonym.delete()
            synonym_count -= 1

    return review, synonym_count


def associate_synonyms_to_vocab(user, vocab, user_specific_json):
    review = None
    synonym_count = 0

    try:
        review = MeaningReview.objects.get(user=user, vocabulary=vocab)
        _, synonym_count = synchronize_synonyms(review, user_specific_json)
    except MeaningReview.DoesNotExist:
        pass

    return review, synonym_count


def get_users_reviews(user):
    return MeaningReview.objects.filter(user=user,
                                        wanikani_srs_numeric__gte=user.profile.get_minimum_wk_srs_threshold_for_review(),
                                        hidden=False)


def get_users_critical_reviews(user):
    return MeaningReview.objects.filter(user=user,
                                        wanikani_srs_numeric__gte=user.profile.get_minimum_wk_srs_threshold_for_review(),
                                        hidden=False,
                                        critical=True)


def get_users_lessons(user):
    return MeaningReview.objects.filter(user=user,
                                        needs_review=True,
                                        wanikani_srs_numeric__gte=user.profile.get_minimum_wk_srs_threshold_for_review(),
                                        hidden=False,
                                        streak=KANIWANI_SRS_LEVELS[KwSrsLevel.UNTRAINED.name][0])


def get_users_current_reviews(user):
    return MeaningReview.objects.filter(user=user,
                                        needs_review=True,
                                        wanikani_srs_numeric__gte=user.profile.get_minimum_wk_srs_threshold_for_review(),
                                        hidden=False,
                                        burned=False,
                                        streak__gte=KANIWANI_SRS_LEVELS[KwSrsLevel.APPRENTICE.name][0])


def get_users_future_reviews(user, time_limit=None):
    queryset = MeaningReview.objects.filter(user=user,
                                            needs_review=False,
                                            wanikani_srs_numeric__gte=user.profile.get_minimum_wk_srs_threshold_for_review(),
                                            hidden=False,
                                            burned=False,
                                            streak__gte=KANIWANI_SRS_LEVELS[KwSrsLevel.APPRENTICE.name][0]).annotate(
        Min('next_review_date')).order_by('next_review_date')

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
    original_length = len(vocab_list)
    vocab_list = [vocab_json for vocab_json in vocab_list if
                  vocab_json['user_specific'] is not None]  # filters out locked items.
    total_unlocked_count = 0
    unlocked_this_request = 0
    for vocabulary_json in vocab_list:
        total_unlocked_count += 1
        _, created, _ = process_single_item_from_wanikani(vocabulary_json, user)
        if created:
            unlocked_this_request += 1

    logger.info("Unlocking level for {}".format(user.username))
    remaining_locked = original_length - total_unlocked_count
    return unlocked_this_request, total_unlocked_count, remaining_locked


def process_single_item_from_wanikani(vocabulary, user):
    user_specific = vocabulary['user_specific']
    vocab, _ = import_vocabulary_from_json(vocabulary)
    review, created = associate_vocab_to_user(vocab, user)
    review, synonyms_added_count = synchronize_synonyms(review, user_specific)
    review.wanikani_srs = user_specific["srs"]
    review.wanikani_srs_numeric = user_specific["srs_numeric"]
    review.wanikani_burned = user_specific["burned"]
    review.save()
    return review, created, synonyms_added_count


def import_vocabulary_from_json(vocabulary):
    vocab, is_new = get_or_create_vocab_by_json(vocabulary)
    vocab = update_local_vocabulary_information(vocab, vocabulary)
    return vocab, is_new


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
    # Filter items the user has not unlocked.
    vocab_list = [vocab_json for vocab_json in vocab_list if vocab_json['user_specific'] is not None]

    for vocabulary_json in vocab_list:
        if user.profile.follow_me:
            review, created, synonyms_added_count = process_single_item_from_wanikani(vocabulary_json, user)
            synonyms_added_count += new_synonym_count
            if created:
                new_review_count += 1
            review.save()
        else: # User does not want to be followed, so we prevent creation of new vocab, and sync only synonyms instead.
            vocabulary = get_or_create_vocab_by_json(vocabulary_json)
            new_review, synonyms_added_count = associate_synonyms_to_vocab(user, vocabulary, vocabulary_json['user_specific'])
            new_synonym_count += synonyms_added_count
    logger.info("Synced Vocabulary for {}".format(user.username))
    return new_review_count, new_synonym_count


def sync_recent_unlocked_vocab_with_wk(user):
    if user.profile.unlocked_levels_list():
        levels = [level for level in range(user.profile.level - 2, user.profile.level + 1) if
                  level in user.profile.unlocked_levels_list()]
        if levels:
            request_string = build_API_sync_string_for_user_for_levels(user, levels)
            try:
                json_data = make_api_call(request_string)
                new_review_count, new_synonym_count = process_vocabulary_response_for_user(user, json_data)
                return new_review_count, new_synonym_count
            except exceptions.InvalidWaniKaniKey:
                user.profile.api_valid = False
                user.profile.save()
            except exceptions.WanikaniAPIException as e:
                logger.warn("Couldn't sync recent vocab for {}".format(user.username), e)
    return 0, 0


def sync_unlocked_vocab_with_wk(user):
    if user.profile.unlocked_levels_list():
        pages = get_level_pages(user.profile.unlocked_levels_list())
        new_review_count = new_synonym_count = 0
        for page in pages:
            request_string = build_API_sync_string_for_user_for_levels(user, page)
            logger.info("Creating sync string for user {}: {}".format(user.username, user.profile.api_key))
            try:
                response = make_api_call(request_string)
                current_page_review_count, current_page_synonym_count = process_vocabulary_response_for_user(user, response)
                new_review_count += current_page_review_count
                new_synonym_count += current_page_synonym_count
            except exceptions.InvalidWaniKaniKey:
                user.profile.api_valid = False
                user.profile.save()
            except exceptions.WanikaniAPIException as e:
                logger.error("Couldn't sync recent vocab for {}".format(user.username), e)
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
        logger.info(user.username + " --- " + str(user.profile.last_visit) + " --- " + str(one_week_ago))
        sync_with_wk.apply_async(args=[user.id, True], queue="long_running_sync")
        affected_count += 1
    return affected_count


def pull_user_synonyms_by_level(user, level):
    '''
    Retrieves vocabulary list from the WK API, specifically searching to pull in synonyms.

    :param user: User to pull WK synonyms or
    :param level: The level for synonyms that should be pulled
    :return: None
    '''
    request_string = build_API_sync_string_for_user_for_levels(user, level)
    try:
        json_data = make_api_call(request_string)
        vocabulary_list = json_data['requested_information']
        for vocabulary in vocabulary_list:
            meaning = vocabulary["meaning"]
            if vocabulary['user_specific'] and vocabulary['user_specific']['user_synonyms']:
                try:
                    review = MeaningReview.objects.get(user=user, vocabulary__meaning=meaning)
                    for synonym in vocabulary['user_specific']['user_synonyms']:
                        review.meaning_synonyms.get_or_create(text=synonym)
                    review.save()
                except MeaningReview.DoesNotExist as e:
                    logger.error("Couldn't pull review during a synonym sync: {}".format(e))
                except KeyError as e:
                    logger.error("No user_specific or synonyms?: {}".format(json_data))
                except MeaningReview.MultipleObjectsReturned:
                    reviews = MeaningReview.objects.filter(user=user, vocabulary__meaning=meaning)
                    for review in reviews:
                        logger.error(
                            "Found something janky! Multiple reviews under 1 vocab meaning?!?: {}".format(
                                review))

    except exceptions.InvalidWaniKaniKey:
        user.profile.api_valid = False
        user.profile.save()
    except exceptions.WanikaniAPIException as e:
        logger.warning("Couldnt pull user synonyms for {}".format(user.username), e)


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
        users_reviews = MeaningReview.objects.filter(user=user)
        elapsed_vacation_time = timezone.now() - vacation_date
        updated_count = users_reviews.update(last_studied=F('last_studied') + elapsed_vacation_time)
        users_reviews.update(next_review_date=F('next_review_date') + elapsed_vacation_time)
        logger.info("brought {} reviews out of hibernation for {}".format(updated_count, user.username))
        logger.info("User {} has been gone for timedelta: {}".format(user.username, str(elapsed_vacation_time)))

    user.profile.vacation_date = None
    user.profile.on_vacation = False
    user.profile.save()
    all_srs(user)


def user_begins_vacation(user):
    user.profile.vacation_date = timezone.now()
    user.profile.save()


def follow_user(user):
    try:
        user.profile.level = get_wanikani_level_by_api_key(user.profile.api_key)
        user.profile.unlocked_levels.get_or_create(level=user.profile.level)
        user.profile.save()
        unlock_eligible_vocab_from_levels(user, user.profile.level)
        sync_user_profile_with_wk(user)
    except exceptions.InvalidWaniKaniKey:
        user.profile.api_valid = False
        user.profile.save()


def disable_follow_me(user):
    user.profile.follow_me = False
    user.profile.save()


def get_24_hour_time_span():
    # Fetch all reviews from now, until just before this hour tomorrow. e.g. ~24 hour span.
    now = timezone.now()
    one_day_from_now = now + timedelta(hours=23)
    one_day_from_now = one_day_from_now.replace(minute=59)
    return now, one_day_from_now


def build_upcoming_srs_for_user(user):
    start, finish = get_24_hour_time_span()
    reviews = get_users_reviews(user).filter(next_review_date__range=(start, finish))

    for review in reviews:
        logger.debug(review.next_review_date)

    reviews = reviews \
        .annotate(hour=TruncHour('next_review_date', tzinfo=timezone.utc)) \
        .annotate(date=TruncDate('next_review_date', tzinfo=timezone.utc)) \
        .values("date", "hour") \
        .annotate(review_count=Count('id')).order_by("date", "hour")

    expected_hour = start.hour
    hours = [hour % 24 for hour in range(expected_hour, expected_hour + 24)]
    retval = OrderedDict.fromkeys(hours, 0)
    for review in reviews:
        found_hour = review['hour'].hour
        while found_hour != expected_hour:
            logger.debug("{} != {}, skipping.".format(found_hour, expected_hour))
            expected_hour = (expected_hour + 1) % 24
        retval[expected_hour] = review["review_count"]
        logger.debug("Inserting reviews at hour {}".format(expected_hour))

    real_retval = [value for key, value in retval.items()]
    return real_retval


def reset_user(user, reset_to_level):
    reset_levels(user, reset_to_level)
    reset_reviews(user, reset_to_level)
    disable_follow_me(user)

    # Set to current level.
    level = get_wanikani_level_by_api_key(user.profile.api_key)
    user.profile.level = level
    user.profile.save()


def reset_levels(user, reset_to_level):
    user.profile.unlocked_levels.filter(level__gte=reset_to_level).delete()
    user.profile.save()


def reset_reviews(user, reset_to_level):
    reviews_to_delete = MeaningReview.objects.filter(user=user)
    reviews_to_delete = reviews_to_delete.exclude(vocabulary__readings__level__lt=reset_to_level)
    reviews_to_delete.delete()
