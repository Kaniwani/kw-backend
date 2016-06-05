from django.contrib.auth.signals import user_logged_in
from kw_webapp.tasks import sync_with_wk


def sync_unlocks_with_wk(sender, **kwargs):
    sync_with_wk(kwargs['user'], full_sync=False)


user_logged_in.connect(sync_unlocks_with_wk)
