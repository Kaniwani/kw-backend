from __future__ import absolute_import

from collections import OrderedDict

from celery import shared_task
from django.contrib.auth.models import User
from django.db.models import F, Count
from django.db.models import Min
from django.db.models.functions import TruncHour, TruncDate
from silk.profiling.profiler import silk_profile
from wanikani_api.exceptions import InvalidWanikaniApiKeyException

from api.sync.SyncerFactory import Syncer
from kw_webapp.constants import KANIWANI_SRS_LEVELS, KwSrsLevel
from kw_webapp.wanikani import exceptions
from kw_webapp.models import UserSpecific, Vocabulary, Profile, Level
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


def get_vocab_by_kanji(kanji):
    v = Vocabulary.objects.filter(readings__character=kanji).distinct()
    number_of_vocabulary = v.count()
    if number_of_vocabulary > 1:
        vocab_ids = ", ".join([str(vocab.id) for vocab in v])
        error = f"Found multiple Vocab with identical kanji with ids: [{vocab_ids}]"
        logger.error(error)
        raise Vocabulary.MultipleObjectsReturned(error)
    elif number_of_vocabulary == 0:
        logger.error(
            f"While attempting to get vocabulary {kanji} we could not find it!"
        )
        raise Vocabulary.DoesNotExist(f"Couldn't find meaning: {kanji}")
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
        logger.error(
            f"While attempting to get vocabulary {meaning} we could not find it!"
        )
        raise Vocabulary.DoesNotExist(f"Couldn't find meaning: {meaning}")
    else:
        return v


def associate_vocab_to_user(vocab, user):
    """
    takes a vocab, and creates a UserSpecific object for the user based on it. Returns the vocab object.
    :param vocab: the vocabulary object to associate to the user.
    :param user: The user.
    :return: the vocabulary object after association to the user
    """
    try:
        review, created = UserSpecific.objects.get_or_create(
            vocabulary=vocab, user=user
        )
        if created:
            review.needs_review = True
            review.next_review_date = timezone.now()
            review.save()
        return review, created

    except UserSpecific.MultipleObjectsReturned:
        us = UserSpecific.objects.filter(vocabulary=vocab, user=user)
        for u in us:
            logger.error(
                f"during {user.username}'s WK sync, we received multiple UserSpecific objects. Details: {u}"
            )
        return None, None


def get_level_pages(levels):
    page_size = 5
    return [
        levels[i : i + page_size] for i in range(0, len(levels), page_size)
    ]


def start_following_wanikani(user):
    try:
        logger.info(f"User {user.username} is toggling on 'Follow Wanikani'")
        syncer = Syncer.factory(user.profile)
        user.profile.level = syncer.get_wanikani_level()
        user.profile.unlocked_levels.get_or_create(level=user.profile.level)
        user.profile.save()
        syncer.sync_user_profile_with_wk
        syncer.unlock_vocab(user.profile.level)
    except exceptions.InvalidWaniKaniKey or InvalidWanikaniApiKeyException as e:
        logger.warning(
            f"User {user.username} failed to toggle Follow Wanikani as they have an invalid API key"
        )
        user.profile.api_valid = False
        user.profile.save()
        raise e


def stop_following_wanikani(user):
    user.profile.follow_me = False
    user.profile.save()


def build_API_sync_string_for_user_for_levels(user, levels):
    return build_API_sync_string_for_api_key_for_levels(
        user.profile.api_key, levels
    )


def build_API_sync_string_for_api_key_for_levels(api_key, levels):
    """
    Given a user, build a vocabulary request string based on their api key, for a particular level.
    :param user: The related user.
    :param level: The level of vocabulary we want to update.
    :return: The fully formatted API string that will provide.
    """
    level_string = (
        ",".join(str(level) for level in levels)
        if isinstance(levels, list)
        else levels
    )
    api_call = f"https://www.wanikani.com/api/user/{api_key}/vocabulary/{level_string}"
    return api_call


def lock_level_for_user(requested_level, user):
    requested_level = int(requested_level)
    reviews = UserSpecific.objects.filter(
        user=user, vocabulary__readings__level=requested_level
    ).distinct()
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
    unlocked_now, unlocked_total, locked = Syncer.factory(
        user.profile
    ).unlock_vocab(level_list)
    return level_list, unlocked_now, unlocked_total, locked


@shared_task
def sync_with_wk(user_id, full=False):
    p = Profile.objects.get(user__id=user_id)
    syncer = Syncer.factory(p)
    return syncer.sync_with_wk(full_sync=full)


def get_users_reviews(user):
    return UserSpecific.objects.filter(
        user=user,
        wanikani_srs_numeric__range=(
            user.profile.get_minimum_wk_srs_threshold_for_review(),
            user.profile.get_maximum_wk_srs_threshold_for_review(),
        ),
        hidden=False,
    )


def get_users_critical_reviews(user):
    return UserSpecific.objects.filter(
        user=user,
        wanikani_srs_numeric__range=(
            user.profile.get_minimum_wk_srs_threshold_for_review(),
            user.profile.get_maximum_wk_srs_threshold_for_review(),
        ),
        hidden=False,
        critical=True,
    )


def get_users_lessons(user):
    qs = UserSpecific.objects.filter(
        user=user,
        needs_review=True,
        wanikani_srs_numeric__range=(
            user.profile.get_minimum_wk_srs_threshold_for_review(),
            user.profile.get_maximum_wk_srs_threshold_for_review(),
        ),
        hidden=False,
        streak=KANIWANI_SRS_LEVELS[KwSrsLevel.UNTRAINED.name][0],
    )

    if user.profile.order_reviews_by_level:
        qs = qs.order_by("vocabulary__readings__level")

    return qs


def get_users_current_reviews(user):
    queryset = UserSpecific.objects.filter(
        user=user,
        needs_review=True,
        wanikani_srs_numeric__range=(
            user.profile.get_minimum_wk_srs_threshold_for_review(),
            user.profile.get_maximum_wk_srs_threshold_for_review(),
        ),
        hidden=False,
        burned=False,
        streak__gte=KANIWANI_SRS_LEVELS[KwSrsLevel.APPRENTICE.name][0],
    )
    if user.profile.order_reviews_by_level:
        queryset = queryset.order_by("vocabulary__readings__level")
    return queryset


def get_users_future_reviews(user, time_limit=None):
    queryset = (
        UserSpecific.objects.filter(
            user=user,
            needs_review=False,
            wanikani_srs_numeric__range=(
                user.profile.get_minimum_wk_srs_threshold_for_review(),
                user.profile.get_maximum_wk_srs_threshold_for_review(),
            ),
            hidden=False,
            burned=False,
            streak__gte=KANIWANI_SRS_LEVELS[KwSrsLevel.APPRENTICE.name][0],
        )
        .annotate(Min("next_review_date"))
        .order_by("next_review_date")
    )

    if isinstance(time_limit, timedelta):
        queryset = queryset.filter(
            next_review_date__lte=timezone.now() + time_limit
        )

    return queryset


def get_all_users_reviews(user):
    min_wk_srs = user.profile.get_minimum_wk_srs_threshold_for_review()
    max_wk_srs = user.profile.get_maximum_wk_srs_threshold_for_review()
    return UserSpecific.objects.filter(
        user=user, wanikani_srs_numeric__range=(min_wk_srs, max_wk_srs)
    )


@shared_task
def sync_all_users_to_wk():
    """
    calls sync_with_wk for all users, causing all users to have their newly unlocked vocabulary synchronized to KW.

    :return: the number of users successfully synced to WK.
    """
    one_week_ago = past_time(24 * 7)
    logger.info("Beginning Bi-daily Sync for all user!")
    users = User.objects.all().exclude(profile__isnull=True)
    logger.info(
        f"Original sync would have occurred for {users.count()} users."
    )
    # Get only users who have recently used WK
    users = User.objects.filter(profile__last_visit__gte=one_week_ago)
    # Get only users who have not lapsed their WK subscription, as we can't query those lapsed users anyhow
    users = users.filter(profile__has_lapsed_wanikani=False)

    logger.info(f"Sync will occur for {users.count()} users.")
    affected_count = 0
    for user in users:
        logger.info(
            f"{user.username} --- {str(user.profile.last_visit)} --- {one_week_ago}"
        )
        sync_with_wk.apply_async(
            args=[user.id, True], queue="long_running_sync"
        )
        affected_count += 1
    logger.info(f"Bi-daily sync tasks kicked off for {affected_count} users")
    return affected_count


def get_24_hour_time_span():
    # Fetch all reviews from now, until just before this hour tomorrow. e.g. ~24 hour span.
    now = timezone.now()
    one_day_from_now = now + timedelta(hours=23)
    one_day_from_now = one_day_from_now.replace(minute=59)
    return now, one_day_from_now


def build_upcoming_srs_for_user(user):
    start, finish = get_24_hour_time_span()
    reviews = get_users_reviews(user).filter(
        next_review_date__range=(start, finish)
    )

    reviews = (
        reviews.annotate(
            hour=TruncHour("next_review_date", tzinfo=timezone.utc)
        )
        .annotate(date=TruncDate("next_review_date", tzinfo=timezone.utc))
        .values("date", "hour")
        .annotate(review_count=Count("id"))
        .order_by("date", "hour")
    )

    logger.debug(f"Building upcoming SRS details for {user.username}")
    expected_hour = start.hour
    hours = [hour % 24 for hour in range(expected_hour, expected_hour + 24)]
    retval = OrderedDict.fromkeys(hours, 0)
    for review in reviews:
        found_hour = review["hour"].hour
        while found_hour != expected_hour:
            logger.debug(f"{found_hour} != {expected_hour}, skipping.")
            expected_hour = (expected_hour + 1) % 24
        retval[expected_hour] = review["review_count"]
        logger.debug(f"Inserting reviews at hour {expected_hour}")
    real_retval = [value for key, value in retval.items()]
    return real_retval


def reset_user(user, reset_to_level):
    logger.info(
        f"{user.username} has requested a reset to level {reset_to_level}"
    )
    reset_levels(user, reset_to_level)
    reset_reviews(user, reset_to_level)
    stop_following_wanikani(user)
    # Set to current level.
    level = Syncer.factory(user.profile).get_wanikani_level()
    user.profile.level = level
    user.profile.save()


def reset_levels(user, reset_to_level):
    logger.info(
        f"{user.username} is having their levels cleared down to {reset_to_level}"
    )
    user.profile.unlocked_levels.filter(level__gte=reset_to_level).delete()
    user.profile.save()


def reset_reviews(user, reset_to_level):
    logger.info(
        f"{user.username} is having their reviews cleared cleared down to level {reset_to_level}"
    )
    reviews_to_delete = UserSpecific.objects.filter(user=user)
    reviews_to_delete = reviews_to_delete.exclude(
        vocabulary__readings__level__lt=reset_to_level
    )
    reviews_to_delete.delete()
