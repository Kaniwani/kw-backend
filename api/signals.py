from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from djoser.signals import user_registered
from rest_framework.authtoken.models import Token

from kw_webapp.tasks import sync_with_wk


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


def sync_unlocks_with_wk(sender, **kwargs):
    if kwargs['user']:
        user = kwargs['user']
        sync_with_wk(user.id, full_sync=user.profile.follow_me)


user_registered.connect(sync_unlocks_with_wk)