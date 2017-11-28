import logging
from itertools import chain

from datetime import timedelta

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.utils import timezone

from kw_webapp import constants
from kw_webapp.constants import TWITTER_USERNAME_REGEX, HTTP_S_REGEX, WkSrsLevel, WANIKANI_SRS_LEVELS

logger = logging.getLogger("kw.models")


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    pub_date = models.DateTimeField('Date Published', auto_now_add=True, null=True)
    creator = models.ForeignKey(User)

    def __str__(self):
        return self.title


class FrequentlyAskedQuestion(models.Model):
    question = models.CharField(max_length=10000)
    answer = models.CharField(max_length=10000)


class Level(models.Model):
    level = models.PositiveIntegerField(validators=[
        MinValueValidator(constants.LEVEL_MIN),
        MaxValueValidator(constants.LEVEL_MAX),
    ])

    def __str__(self):
        return str(self.level)


class Profile(models.Model):
    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
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
    last_visit = models.DateTimeField(null=True, auto_now_add=True)
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
    minimum_wk_srs_level_to_review = models.CharField(max_length=20, choices=WkSrsLevel.choices(),
                                                      default=WkSrsLevel.APPRENTICE.name)

    # Vacation Settings
    on_vacation = models.BooleanField(default=False)
    vacation_date = models.DateTimeField(default=None, null=True, blank=True)

    def get_minimum_wk_srs_threshold_for_review(self):
        minimum_wk_srs = self.minimum_wk_srs_level_to_review
        minimum_streak = WANIKANI_SRS_LEVELS[minimum_wk_srs][0]
        return minimum_streak

    def set_twitter_account(self, twitter_account):
        if not twitter_account:
            return

        if twitter_account.startswith("@") and TWITTER_USERNAME_REGEX.match(twitter_account[1:]):
            self.twitter = twitter_account
        elif TWITTER_USERNAME_REGEX.match(twitter_account):
            self.twitter = "@{}".format(twitter_account)
        else:
            logger.warning("WK returned a funky twitter account name: {},  for user:{} ".format(twitter_account,
                                                                                                self.user.username))

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
        self.level = new_level
        self.save()

    def __str__(self):
        return "{} -- {} -- {} -- {}".format(self.user.username, self.api_key, self.level, self.unlocked_levels_list())


class Vocabulary(models.Model):
    meaning = models.CharField(max_length=255)

    def reading_count(self):
        return self.readings.all().count()

    def available_readings(self, level):
        return self.readings.filter(level__lte=level)

    def get_absolute_url(self):
        return "https://www.wanikani.com/vocabulary/{}/".format(self.readings.all()[0])

    def __str__(self):
        return self.meaning


class Tag(models.Model):
    """
    A model meant to handle tagging readings.
    """
    name = models.CharField(max_length=255, unique=True)

    def get_all_vocabulary(self):
        return Vocabulary.objects.filter(readings__tags__id=self.id).distinct()

    def __str__(self):
        return self.name

class PartOfSpeech(models.Model):
    part = models.CharField(max_length=30)

    def __str__(self):
        return str(self.part)

class Report(models.Model):
    created_by = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    vocabulary = models.ForeignKey(Vocabulary)
    reason = models.CharField(max_length=1000)

    def __str__(self):
        return "Issue with {}, reported by {} at {}. Reason: {}".format(self.vocabulary.meaning,
                                                                        self.created_by.username,
                                                                        self.created_at,
                                                                        self.reason)

class Reading(models.Model):
    vocabulary = models.ForeignKey(Vocabulary, related_name='readings', on_delete=models.CASCADE)
    character = models.CharField(max_length=255)
    kana = models.CharField(max_length=255)
    level = models.PositiveIntegerField(null=True, validators=[
        MinValueValidator(constants.LEVEL_MIN),
        MaxValueValidator(constants.LEVEL_MAX),
    ])

    # JISHO information
    sentence_en = models.CharField(max_length=1000, null=True)
    sentence_ja = models.CharField(max_length=1000, null=True)
    common = models.NullBooleanField()
    tags = models.ManyToManyField(Tag)
    furigana = models.CharField(max_length=100, null=True)
    pitch = models.CharField(max_length=100, null=True)
    parts_of_speech = models.ManyToManyField(PartOfSpeech)

    def __str__(self):
        return "{} - {} - {} - {}".format(self.vocabulary.meaning, self.kana, self.character, self.level)


class UserSpecific(models.Model):
    vocabulary = models.ForeignKey(Vocabulary)
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    correct = models.PositiveIntegerField(default=0)
    incorrect = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    last_studied = models.DateTimeField(blank=True, null=True)
    needs_review = models.BooleanField(default=True)
    unlock_date = models.DateTimeField(default=timezone.now, blank=True)
    next_review_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    burned = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    wanikani_srs = models.CharField(max_length=255, default="unknown")
    wanikani_srs_numeric = models.IntegerField(default=0)
    wanikani_burned = models.BooleanField(default=False)
    notes = models.CharField(max_length=500, editable=True, blank=True, null=True)
    critical = models.BooleanField(default=False)

    class Meta:
        unique_together = ('vocabulary', 'user')

    def answered_correctly(self, first_try=True):
        if first_try:
            self.correct += 1
            self.streak += 1
            if self.streak >= constants.WANIKANI_SRS_LEVELS[WkSrsLevel.BURNED.name][0]:
                self.burned = True

        self.needs_review = False
        self.last_studied = timezone.now()
        self.set_next_review_time()
        self.set_criticality()
        self.save()

    def answered_incorrectly(self):
        """
        Helper function to correctly decrement streak value and increase count of incorrect.
        If user is nearing burned status, they get doubly-decremented.
        """
        self.incorrect += 1
        # If user is about to burn, drop them two levels.
        if self.streak == 7:
            self.streak -= 2
        # streak of 0 indicates "Lesson" and we don't want users dropping down to lesson.
        elif self.streak > 1:
            self.streak -= 1

        self.streak = max(0, self.streak)
        self.save()
        self.set_criticality()

    def set_criticality(self):
        if self.is_critical():
            self.critical = True
        else:
            self.critical = False

    def _can_be_critical(self):
        return self.correct + self.incorrect >= constants.MINIMUM_ATTEMPT_COUNT_FOR_CRITICALITY

    def _breaks_threshold(self):
        return float(self.incorrect) / float(self.correct + self.incorrect) >= constants.CRITICALITY_THRESHOLD

    def is_critical(self):
        if self._can_be_critical() and self._breaks_threshold():
            return True
        else:
            return False

    def get_all_readings(self):
        return list(chain(self.vocabulary.readings.all(), self.answer_synonyms.all()))

    def can_be_managed_by(self, user):
        return self.user == user or user.is_superuser

    def synonyms_list(self):
        return [synonym.text for synonym in self.meaningsynonym_set.all()]

    def synonyms_string(self):
        return ", ".join([synonym.text for synonym in self.meaningsynonym_set.all()])

    def remove_synonym(self, text):
        self.meaningsynonym_set.remove(MeaningSynonym.objects.get(text=text))

    def answer_synonyms_list(self):
        return [synonym.kana for synonym in self.answer_synonyms.all()]

    def add_answer_synonym(self, kana, character):
        synonym, created = self.answer_synonyms.get_or_create(kana=kana, character=character)
        return synonym, created

    def set_next_review_time(self):
        if self.streak not in constants.SRS_TIMES.keys():
            self.next_review_date = None
        else:
            self.next_review_date = timezone.now() + timedelta(hours=constants.SRS_TIMES[self.streak])
            self._round_review_time_up()
        self.save()

    def set_next_review_time_based_on_last_studied(self):
        self.next_review_date = self.last_studied + timedelta(hours=constants.SRS_TIMES[self.streak])
        self._round_review_time_up()
        self.save()

    def _round_next_review_date(self):
        round_to = constants.REVIEW_ROUNDING_TIME.total_seconds()
        seconds = (
            self.next_review_date - self.next_review_date.min.replace(tzinfo=self.next_review_date.tzinfo)).seconds
        rounding = (seconds + round_to) // round_to * round_to
        self.next_review_date = self.next_review_date + timedelta(0, rounding - seconds, 0)
        self.save()

    def _round_last_studied_date(self):
        round_to = constants.REVIEW_ROUNDING_TIME.total_seconds()
        seconds = (self.last_studied - self.last_studied.min.replace(tzinfo=self.last_studied.tzinfo)).seconds
        rounding = (seconds + round_to) // round_to * round_to
        self.last_studied = self.last_studied + timedelta(0, rounding - seconds, 0)
        self.save()

    def _round_review_time_up(self):
        self._round_next_review_date()
        self._round_last_studied_date()

    def __str__(self):
        return "{} - {} - {} - c:{} - i:{} - s:{} - ls:{} - nr:{} - uld:{}".format(self.id,
                                                                                   self.vocabulary.meaning,
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
    review = models.ForeignKey(UserSpecific, related_name="answer_synonyms", null=True)

    def __str__(self):
        return "{} - {} - {} - SYNONYM".format(self.review.vocabulary.meaning, self.kana, self.character)

    def as_dict(self):
        return {
            "id": self.id,
            "kana": self.kana,
            "character": self.character,
            "review_id": self.review.id
        }


class MeaningSynonym(models.Model):
    text = models.CharField(max_length=255, blank=False, null=False)
    review = models.ForeignKey(UserSpecific, null=True)

    def __str__(self):
        return self.text
