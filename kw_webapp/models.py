from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import  User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.signals import user_logged_in, user_logged_out
import requests


class Profile(models.Model):
    user = models.OneToOneField(User)
    api_key = models.CharField(max_length=255)
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

class UserSpecific(models.Model):
    vocabulary = models.ForeignKey(Vocabulary)
    user = models.ForeignKey(User)
    correct = models.PositiveIntegerField()
    incorrect = models.PositiveIntegerField()
    streak = models.PositiveIntegerField()
    last_studied = models.DateTimeField()


#User object is passed along in the call.
def update_user_level(sender, **kwargs):
    r = requests.get("https://www.wanikani.com/api/user/{}/user-information".format(kwargs['user'].profile.api_key))
    if r.status_code == 200:
        json_data = r.json()
        user_info = json_data["user_information"]
        level = user_info["level"]
        wk_username = user_info["username"]
        gravatar = user_info["gravatar"]
        kwargs['user'].profile.level = level
        kwargs['user'].profile.save()




    print(r.text)

user_logged_in.connect(update_user_level)