from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from djoser.signals import user_registered
from rest_framework.authtoken.models import Token

from api.sync.SyncerFactory import Syncer
from kw_webapp import constants
from kw_webapp.tasks import sync_with_wk, get_users_lessons

import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


def sync_unlocks_with_wk(sender, **kwargs):
    if kwargs["user"]:
        user = kwargs["user"]
        sync_with_wk(user.id, full=user.profile.follow_me)
        if user_still_has_no_lessons(user):
            unlock_previous_level(user)


def user_still_has_no_lessons(user):
    return get_users_lessons(user).count() == 0


def unlock_previous_level(user):
    user.profile.refresh_from_db()
    if user.profile.level == constants.LEVEL_MIN:
        return
    else:
        previous_level = user.profile.level - 1
        user.profile.unlocked_levels.get_or_create(level=previous_level)
        syncer = Syncer.factory(user.profile)
        syncer.unlock_vocab(previous_level)


user_registered.connect(sync_unlocks_with_wk)
