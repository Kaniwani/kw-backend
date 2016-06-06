import requests
from django.utils import timezone

from kw_webapp import constants
from kw_webapp.models import UserSpecific, Profile
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
