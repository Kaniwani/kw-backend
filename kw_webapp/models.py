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
        MaxValueValidator(60),
    ])

    def __str__(self):
        return str(self.level)


class Profile(models.Model):
    user = models.OneToOneField(User)
    api_key = models.CharField(max_length=255)
    api_valid = models.BooleanField(default=False)
    gravatar = models.CharField(max_length=255)
    about = models.CharField(max_length=255, default="")
    website = models.CharField(max_length=255, default="")
    twitter = models.CharField(max_length=255, default="@Tadgh11")
    topics_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(null=True, validators=[
        MinValueValidator(1),
        MaxValueValidator(60),
    ])
    unlocked_levels = models.ManyToManyField(Level)

    def unlocked_levels_list(self):
        x = self.unlocked_levels.values_list('level')
        return x
    
    def __str__(self):
        return "{} -- {} -- {} -- {}".format(self.user.username, self.api_key, self.level, self.unlocked_levels_list())


class Vocabulary(models.Model):
    meaning = models.CharField(max_length=255)

    def reading_count(self):
        return self.reading_set.all().count()

    def available_readings(self, level):
        return self.reading_set.filter(level__lte=level)

    def get_absolute_url(self):
        return "https://www.wanikani.com/vocabulary/{}/".format(self.reading_set.all()[0])

    def __str__(self):
        return self.meaning


class Reading(models.Model):
    vocabulary = models.ForeignKey(Vocabulary)
    character = models.CharField(max_length=255)
    kana = models.CharField(max_length=255)
    level = models.PositiveIntegerField(validators=[
        MinValueValidator(1),
        MaxValueValidator(60),
    ])


    def __str__(self):
        return "{} - {} - {} - {}".format(self.vocabulary.meaning, self.kana, self.character, self.level)


class UserSpecific(models.Model):
    vocabulary = models.ForeignKey(Vocabulary)
    synonyms = models.CharField(max_length=255, default=None, blank=True, null=True)
    user = models.ForeignKey(User)
    correct = models.PositiveIntegerField(default=0)
    incorrect = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    last_studied = models.DateTimeField(auto_now_add=True, blank=True)
    needs_review = models.BooleanField(default=True)
    unlock_date = models.DateTimeField(default=timezone.now, blank=True)
    next_review_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    burnt = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)

    def synonyms_list(self):
        return [synonym.text for synonym in self.synonym_set.all()]

    def synonyms_string(self):
        return ",".join([synonym.text for synonym in self.synonym_set.all()])

    def remove_synonym(self, text):
        self.synonym_set.remove(Synonym.objects.get(text=text))

    def __str__(self):
        return "{} - {} - c:{} - i:{} - s:{} - ls:{} - nr:{} - uld:{}".format(self.vocabulary.meaning,
                                                                     self.user.username,
                                                                     self.correct,
                                                                     self.incorrect,
                                                                     self.streak,
                                                                     self.last_studied,
                                                                     self.needs_review,
                                                                     self.unlock_date)


class Synonym(models.Model):
    text = models.CharField(max_length=255, blank=False, null=False)
    review = models.ForeignKey(UserSpecific, null=True)

    def __str__(self):
        return self.text
