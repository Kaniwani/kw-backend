import logging
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from django.utils.encoding import smart_str
import requests


logger = logging.getLogger("kw.models")


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    pub_date = models.DateTimeField('Date Published', default=timezone.now(), null=True)
    creator = models.ForeignKey(User)

    def __str__(self):
        return self.title


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


