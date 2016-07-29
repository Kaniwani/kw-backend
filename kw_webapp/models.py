import logging
from itertools import chain

from datetime import timedelta

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.utils import timezone

from kw_webapp import constants
from kw_webapp.constants import TWITTER_USERNAME_REGEX, HTTP_S_REGEX

logger = logging.getLogger("kw.models")


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    pub_date = models.DateTimeField('Date Published', auto_now_add=True, null=True)
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
    api_valid = models.BooleanField(default=True)
    gravatar = models.CharField(max_length=255)
    about = models.CharField(max_length=255, default="")
    website = models.CharField(max_length=255, default="N/A", null=True)
    twitter = models.CharField(max_length=255, default="N/A", null=True)
    topics_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=255, default="Turtles", null=True)
    join_date = models.DateField(auto_now_add=True, null=True)
    last_wanikani_sync_date = models.DateTimeField(auto_now_add=True, null=True)
    level = models.PositiveIntegerField(null=True, validators=[
        MinValueValidator(constants.LEVEL_MIN),
        MaxValueValidator(constants.LEVEL_MAX),
    ])

    # General user-changeable settings
    unlocked_levels = models.ManyToManyField(Level)
    follow_me = models.BooleanField(default=True)
    auto_advance_on_success = models.BooleanField(default=False)
    auto_expand_answer_on_success = models.BooleanField(default=False)
    auto_expand_answer_on_failure = models.BooleanField(default=False)
    only_review_burned = models.BooleanField(default=False)

    # Vacation Settings
    on_vacation = models.BooleanField(default=False)
    vacation_date = models.DateTimeField(default=None, null=True, blank=True)

    def set_twitter_account(self, twitter_account):
        if not twitter_account:
            return

        if twitter_account.startswith("@") and TWITTER_USERNAME_REGEX.match(twitter_account[1:]):
            self.twitter = twitter_account
        elif TWITTER_USERNAME_REGEX.match(twitter_account):
            self.twitter = "@{}".format(twitter_account)
        else:
            logger.warning("WK returned a funky twitter account name: {},  for user:{} ".format(twitter_account, self.user.username))

        self.save()

    def set_website(self, website_url):
        if website_url:
            fixed_site = HTTP_S_REGEX.sub("", website_url)
            if fixed_site:
                self.website = fixed_site
                self.save()

    def unlocked_levels_list(self):
        x = self.unlocked_levels.values_list('level')
        x = [x[0] for x in x]
        return x

    def handle_wanikani_level_change(self, new_level):
        original_level = self.level
        self.level = new_level
        self.save()

        #The case of a user resetting their WK profile.
        if new_level < original_level:
            expired_levels = self.unlocked_levels.filter(level__gt=new_level)
            expired_levels.delete()

            expired_reviews = self.get_overleveled_reviews()
            expired_reviews.delete()

    def get_overleveled_reviews(self):
        return UserSpecific.objects.filter(user=self.user, vocabulary__reading__level__gt=self.user.profile.level)

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
    level = models.PositiveIntegerField(null=True, validators=[
        MinValueValidator(constants.LEVEL_MIN),
        MaxValueValidator(constants.LEVEL_MAX),
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
    unlock_date = models.DateTimeField(default=timezone.now, blank=True)
    next_review_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    burned = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    wanikani_srs = models.CharField(max_length=255, default="unknown")
    wanikani_srs_numeric = models.IntegerField(default=0)
    wanikani_burned = models.BooleanField(default=False)

    def get_all_readings(self):
        return list(chain(self.vocabulary.reading_set.all(), self.answersynonym_set.all()))

    def can_be_managed_by(self, user):
        return self.user == user or user.is_superuser

    def synonyms_list(self):
        return [synonym.text for synonym in self.meaningsynonym_set.all()]

    def synonyms_string(self):
        return ", ".join([synonym.text for synonym in self.meaningsynonym_set.all()])

    def remove_synonym(self, text):
        self.meaningsynonym_set.remove(MeaningSynonym.objects.get(text=text))

    def answer_synonyms(self):
        return [synonym.kana for synonym in self.answersynonym_set.all()]

    def add_answer_synonym(self, kana, character):
        synonym, created = self.answersynonym_set.get_or_create(kana=kana, character=character)
        return synonym, created

    def set_next_review_time(self):
        self.next_review_date = timezone.now() + timedelta(hours=constants.SRS_TIMES[self.streak])
        self._round_review_time_up()
        self.save()

    def set_next_review_time_based_on_last_studied(self):
        self.next_review_date = self.last_studied + timedelta(hours=constants.SRS_TIMES[self.streak])
        self._round_review_time_up()
        self.save()

    def _round_review_time_up(self):
        original_date = self.next_review_date
        round_to = constants.REVIEW_ROUNDING_TIME.total_seconds()
        seconds = (
            self.next_review_date - self.next_review_date.min.replace(tzinfo=self.next_review_date.tzinfo)).seconds
        rounding = (seconds + round_to) // round_to * round_to
        self.next_review_date = self.next_review_date + timedelta(0, rounding - seconds, 0)

        logger.debug(
            "Updating Next Review Time for user {} for review {}. Went from {} to {}, a rounding of {:.1f} minutes"
                .format(self.user,
                        self.vocabulary.meaning,
                        original_date.strftime("%H:%M:%S"),
                        self.next_review_date.strftime("%H:%M:%S"),
                        (self.next_review_date - original_date).total_seconds() / 60))
        self.save()

    def __str__(self):
        return "{} - {} - c:{} - i:{} - s:{} - ls:{} - nr:{} - uld:{}".format(self.vocabulary.meaning,
                                                                              self.user.username,
                                                                              self.correct,
                                                                              self.incorrect,
                                                                              self.streak,
                                                                              self.last_studied,
                                                                              self.needs_review,
                                                                              self.unlock_date)


class AnswerSynonym(models.Model):
    character = models.CharField(max_length=255, null=True)
    kana = models.CharField(max_length=255, null=False)
    review = models.ForeignKey(UserSpecific, null=True)

    def __str__(self):
        return "{} - {} - {} - SYNONYM".format(self.review.vocabulary.meaning, self.kana, self.character)

    def as_dict(self):
        return {
            "id": self.id,
            "kana": self.kana,
            "character": self.character,
            "user_specific_id": self.review.id
        }


class MeaningSynonym(models.Model):
    text = models.CharField(max_length=255, blank=False, null=False)
    review = models.ForeignKey(UserSpecific, null=True)

    def __str__(self):
        return self.text
