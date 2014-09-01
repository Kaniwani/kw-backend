from django.contrib.auth.signals import user_logged_in, user_logged_out
from kw_webapp.tasks import sync_with_wk


def sync_unlocks_with_wk(sender, **kwargs):
    sync_with_wk.delay(kwargs['user'])


user_logged_in.connect(sync_unlocks_with_wk)
