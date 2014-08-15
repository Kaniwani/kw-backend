from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from django.utils.encoding import smart_str
import requests


class Profile(models.Model):
    user = models.OneToOneField(User)
    api_key = models.CharField(max_length=255)
    gravatar = models.CharField(max_length=255)
    level = models.PositiveIntegerField(null=True, validators=[
        MinValueValidator(1),
        MaxValueValidator(50),
    ])


class Vocabulary(models.Model):
    meaning = models.CharField(max_length=255)

    def num_options(self):
        return self.reading_set.all().count()


class Reading(models.Model):
    vocabulary = models.ForeignKey(Vocabulary)
    character = models.CharField(max_length=255)
    kana = models.CharField(max_length=255)
    level = models.PositiveIntegerField(validators=[
        MinValueValidator(1),
        MaxValueValidator(50),
    ])

    def __str__(self):
        return "{} - {} - {}".format(self.vocabulary.meaning, self.kana, self.character)


class UserSpecific(models.Model):
    vocabulary = models.ForeignKey(Vocabulary)
    user = models.ForeignKey(User)
    correct = models.PositiveIntegerField(default=0)
    incorrect = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    last_studied = models.DateTimeField(auto_now_add=True, blank=True)
    needs_review = models.BooleanField(default=True)

    def __str__(self):
        return "{} - {} - c:{} - i:{} - s:{} - ls:{} - nr:{}".format(self.vocabulary.meaning,
                                                                     self.user.username,
                                                                     self.correct,
                                                                     self.incorrect,
                                                                     self.streak,
                                                                     self.last_studied,
                                                                     self.needs_review)


# User object is passed along in the call.
def update_user_level(sender, **kwargs):
    r = requests.get(
        "https://www.wanikani.com/api/user/{}/user-information".format(kwargs['user'].profile.api_key))
    if r.status_code == 200:
        json_data = r.json()
        user_info = json_data["user_information"]
        level = user_info["level"]
        gravatar = user_info["gravatar"]
        kwargs['user'].profile.level = level
        kwargs['user'].profile.gravatar = gravatar
        kwargs['user'].profile.save()


def sync_unlocks_with_wk(sender, **kwargs):
    print("SYNCING WITH WK")
    user = kwargs['user']
    r = requests.get("https://www.wanikani.com/api/user/{}/vocabulary/{}".format(
        user.profile.api_key, user.profile.level))
    if r.status_code == 200:
        json_data = r.json()
        for vocabulary in json_data['requested_information']:
            if vocabulary['user_specific'] is not None:
                v = Vocabulary.objects.get(meaning=vocabulary['meaning'])
                u_s, created = UserSpecific.objects.get_or_create(
                    vocabulary=v, user=user)
                if created:
                    pass


user_logged_in.connect(update_user_level)
user_logged_in.connect(sync_unlocks_with_wk)
