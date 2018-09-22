from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save

from kw_webapp import constants
from kw_webapp.models import Profile
from kw_webapp.tasks import sync_with_wk, get_users_lessons, unlock_eligible_vocab_from_levels


def sync_unlocks_with_wk(sender, **kwargs):
    if kwargs["user"]:
        user = kwargs["user"]
        sync_with_wk.delay(user.id, full_sync=user.profile.follow_me)


def unlock_default_level_for_user(sender, instance, created, **kwargs):
    if not created:
        return
    user = instance.user
    sync_with_wk(user.id)
    if user_still_has_no_lessons(user):
        unlock_previous_level(user)


def user_still_has_no_lessons(user):
    return get_users_lessons(user).count() == 0


def unlock_previous_level(user):
    if user.profile.level == constants.LEVEL_MIN:
        return
    else:
        unlock_eligible_vocab_from_levels(user, user.profile.level - 1)



user_logged_in.connect(sync_unlocks_with_wk)
post_save.connect(unlock_default_level_for_user, sender=Profile)
