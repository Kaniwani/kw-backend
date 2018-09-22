from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save

from kw_webapp import constants
from kw_webapp.models import Profile
from kw_webapp.tasks import sync_with_wk, get_users_lessons, unlock_eligible_vocab_from_levels


def sync_unlocks_with_wk(sender, **kwargs):
    if kwargs["user"]:
        user = kwargs["user"]
        sync_with_wk.delay(user.id, full_sync=user.profile.follow_me)

user_logged_in.connect(sync_unlocks_with_wk)
