import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from kw_webapp.models import UserSpecific

logger = logging.getLogger(__name__)


@shared_task
def all_srs(user=None):
    """
    Task that performs an SRS update for users. Checks user current streak and last_reviewed_date in order to determine
    when the next review should be. If the time for the review is in the past, flag it for review for the user.

    :param user: Optional Param, the user to be updated. If left blank, will update all users.
    :return: None
    """
    related_username = user.username if user else "all users"
    # logger.info(f"Beginning  SRS run for {related_username}")
    affected_count = 0
    now = timezone.now()
    slightly_ahead_of_now = now + timedelta(minutes=1)

    # Fetches all reviews with next_review_date greater than or equal to NOW, flips them all to needs_review=True
    if user and user.profile.on_vacation:
        logger.info(
            f"Skipping SRS for user {user.username} as they are on vacation as of {user.profile.vacation_date}"
        )
        return 0

    if user:
        review_set = UserSpecific.objects.filter(
            user=user,
            next_review_date__lte=slightly_ahead_of_now,
            needs_review=False,
        )
    else:
        review_set = UserSpecific.objects.filter(
            user__profile__on_vacation=False,
            next_review_date__lte=slightly_ahead_of_now,
            needs_review=False,
        )

    affected_count += review_set.update(needs_review=True)
    logger.info(
        f"User {user.username if user else 'all users'} has {affected_count} new reviews."
    )
    return affected_count
