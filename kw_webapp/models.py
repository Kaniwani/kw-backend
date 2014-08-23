import logging
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from django.utils.encoding import smart_str
import requests

logger = logging.getLogger("kw.models")


class Level(models.Model):
    level = models.PositiveIntegerField(validators=[
        MinValueValidator(1),
        MaxValueValidator(50),
    ])


class Profile(models.Model):
    user = models.OneToOneField(User)
    api_key = models.CharField(max_length=255)
    gravatar = models.CharField(max_length=255)
    level = models.PositiveIntegerField(null=True, validators=[
        MinValueValidator(1),
        MaxValueValidator(50),
    ])
    unlocked_levels = models.ManyToManyField(Level)

    def unlocked_levels_list(self):
        x = self.unlocked_levels.values_list('level')
        return x


class Vocabulary(models.Model):
    meaning = models.CharField(max_length=255)

    def num_options(self):
        return self.reading_set.all().count()

    def available_readings(self, level):
        return self.reading_set.filter(level__lte=level)

    def get_absolute_url(self):
        return "https://www.wanikani.com/vocabulary/{}/".format(self.reading_set.all()[0])



class Reading(models.Model):
    vocabulary = models.ForeignKey(Vocabulary)
    character = models.CharField(max_length=255)
    kana = models.CharField(max_length=255)
    level = models.PositiveIntegerField(validators=[
        MinValueValidator(1),
        MaxValueValidator(50),
    ])

    def __str__(self):
        return "{} - {} - {} - {}".format(self.vocabulary.meaning, self.kana, self.character, self.level)



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
    user = kwargs['user']
    logger.info("{} began Syncing user data from WK...".format(user.username))
    r = requests.get(
        "https://www.wanikani.com/api/user/{}/user-information".format(kwargs['user'].profile.api_key))
    if r.status_code == 200:
        json_data = r.json()
        user_info = json_data["user_information"]

        user.profile.level = user_info["level"]
        user.profile.unlocked_levels.get_or_create(level=user_info["level"])
        user.profile.gravatar = user_info["gravatar"]
        user.profile.save()

        logger.info("{} finished Syncing user data from WK.".format(user.username))
    else:
        logger.error("Issue communicating with WK API. User {} with api_key {} ".format(user.username, user.profile.api_key))


def sync_unlocks_with_wk(sender, **kwargs):
    logger.info("Beginning WK sync for user")
    user = kwargs['user']
    logger.info("{} has begun Syncing with WK...".format(user.username))
    r = requests.get("https://www.wanikani.com/api/user/{}/vocabulary/{}".format(
        user.profile.api_key, user.profile.level))
    if r.status_code == 200:
        json_data = r.json()
        for vocabulary in json_data['requested_information']:
            #user_specific is None until the user actually unlocks it in WK. This allows us to sync perfectly with what
            #the user currently has unlocked.
            if vocabulary['user_specific'] is not None:
                #This will cause issues if WK ever updates their vocabulary limit.
                try:
                    v = Vocabulary.objects.get(meaning=vocabulary['meaning'])
                except Vocabulary.DoesNotExist:
                    logger.error("While attempting to get vocabulary {} we could not find it!".format(vocabulary['meaning']))
                    continue
                try:
                    u_s, created = UserSpecific.objects.get_or_create(vocabulary=v, user=user)
                    if created:
                        logger.info("{} just unlocked {} from WK.".format(user.username, u_s.vocabulary.meaning))
                        u_s.needs_review = True
                        u_s.save()
                except UserSpecific.MultipleObjectsReturned:
                    us = UserSpecific.objects.filter(vocabulary=v, user=user)
                    for u in us:
                        logger.error("during {}'s WK sync, we received multiple UserSpecific objects. Details: {}".format(u))



user_logged_in.connect(update_user_level)
user_logged_in.connect(sync_unlocks_with_wk)
