from __future__ import absolute_import
import logging
from KW.celery import app as celery_app
from kw_webapp.models import UserSpecific
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
def srs_four_hours():
    cutoff_time = past_time(4)
    to_be_reviewed = UserSpecific.objects.filter(last_studied__lte=cutoff_time, streak=0)
    return to_be_reviewed

@celery_app.task()
def srs_eight_hours():
    cutoff_time = past_time(8)
    to_be_reviewed = UserSpecific.objects.filter(last_studied__lte=cutoff_time, streak=1)
    return to_be_reviewed


@celery_app.task()
def srs_one_day():
    cutoff_time = past_time(24)
    to_be_reviewed = UserSpecific.objects.filter(last_studied__lte=cutoff_time, streak=2)
    return to_be_reviewed


@celery_app.task()
def srs_three_days():
    cutoff_time = past_time(72)
    to_be_reviewed = UserSpecific.objects.filter(last_studied__lte=cutoff_time, streak=3)
    return to_be_reviewed


@celery_app.task()
def srs_one_week():
    cutoff_time = past_time(168)
    to_be_reviewed = UserSpecific.objects.filter(last_studied__lte=cutoff_time, streak=4)
    return to_be_reviewed


@celery_app.task()
def srs_two_weeks():
    cutoff_time = past_time(336)
    to_be_reviewed = UserSpecific.objects.filter(last_studied__lte=cutoff_time, streak=5)
    return to_be_reviewed


@celery_app.task()
def srs_one_month():
    cutoff_time = past_time(720)
    to_be_reviewed = UserSpecific.objects.filter(last_studied__lte=cutoff_time, streak=6)
    return to_be_reviewed


@celery_app.task()
def srs_three_months():
    cutoff_time = past_time(2160)
    to_be_reviewed = UserSpecific.objects.filter(last_studied__lte=cutoff_time, streak=7)
    return to_be_reviewed


@celery_app.task()
def all_srs(user=None):
    logger.info("Beginning SRS run for {}.".format(user or "all users"))
    hours = [4, 8, 24, 72, 168, 336, 720, 2160]
    srs_level = zip(map(lambda x: past_time(x), hours), range(0, 8))
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
            logger.info("SRS level {} for {} had {} updates set".format(level[1], (user or "all users"),  review_set.count()))
        else:
            logger.info("{} has no reviews for SRS level {}".format((user or "all users"), level[1]))
        review_set.update(needs_review=True)
    logger.info("Finished SRS run for {}.".format(user or "all users"))