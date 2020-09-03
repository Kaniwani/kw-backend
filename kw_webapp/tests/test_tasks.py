import re
from copy import deepcopy

import responses
import time
from django.test import TestCase
from django.utils import timezone

from api.sync.SyncerFactory import Syncer
from api.sync.WanikaniUserSyncerV2 import WanikaniUserSyncerV2
from kw_webapp import constants
from kw_webapp.models import (
    Vocabulary,
    UserSpecific,
    MeaningSynonym,
    AnswerSynonym,
)
from kw_webapp.srs import all_srs
from kw_webapp.tasks import (
    past_time,
    associate_vocab_to_user,
    lock_level_for_user,
    unlock_all_possible_levels_for_user,
    get_users_future_reviews,
    sync_all_users_to_wk,
    reset_user,
    get_users_current_reviews,
    reset_levels,
    get_users_lessons,
    get_vocab_by_kanji,
    get_level_pages,
    sync_with_wk,
)
from kw_webapp.tests import sample_api_responses_v2
from kw_webapp.tests.utils import (
    create_review,
    create_vocab,
    create_user,
    create_profile,
    create_reading,
)
from kw_webapp.utils import generate_user_stats


class TestTasks(TestCase):
    def setUp(self):
        self.user = create_user("Tadgh")
        create_profile(self.user, "any_key", 5)
        self.vocabulary = create_vocab("radioactive bat")
        self.reading = create_reading(self.vocabulary, "ねこ", "猫", 2)
        self.review = create_review(self.vocabulary, self.user)
        self._vocab_api_regex = re.compile(
            r"https://www\.wanikani\.com/api/user/.*"
        )

    def testLevelPageCreator(self):
        flat_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        pages = get_level_pages(flat_list)
        self.assertEqual(len(pages), 2)
        self.assertListEqual(pages[0], [1, 2, 3, 4, 5])
        self.assertListEqual(pages[1], [6, 7, 8, 9, 10])

    def test_userspecifics_needing_review_are_flagged(self):
        self.review.needs_review = False
        self.review.last_studied = past_time(5)
        self.review.save()
        all_srs()
        review = UserSpecific.objects.get(pk=self.review.id)
        self.assertTrue(review.needs_review)

    def test_associate_vocab_to_user_successfully_creates_review(self):
        new_vocab = create_vocab("dishwasher")

        review, created = associate_vocab_to_user(new_vocab, self.user)

        self.assertTrue(review.needs_review is True)
        self.assertTrue(created)

    def test_locking_level_removes_all_reviews_at_that_level(self):
        self.vocabulary.readings.create(
            level=5, kana="猫", character="whatever"
        )
        self.vocabulary.readings.create(
            level=5, kana="猫二", character="whatever2"
        )

        lock_level_for_user(5, self.user)

        available_reviews = UserSpecific.objects.filter(
            user=self.user, vocabulary__readings__level=5
        ).all()
        self.assertFalse(available_reviews)

    def test_locking_level_removes_level_from_unlocked_list(self):
        self.user.profile.unlocked_levels.get_or_create(level=7)
        self.user.profile.unlocked_levels.get_or_create(level=6)
        self.vocabulary.readings.create(
            level=6, kana="猫二", character="whatever2"
        )

        lock_level_for_user(6, self.user)
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [5, 7])

    @responses.activate
    def test_creating_new_synonyms_on_sync(self):
        pass

    def test_users_who_are_on_vacation_are_ignored_by_all_srs_algorithm(self):
        self.review.last_studied = past_time(10)
        self.review.streak = 1
        self.review.needs_review = False
        self.review.save()

        reviews_affected = all_srs()
        self.assertEqual(reviews_affected, 1)

        self.review.last_studied = past_time(10)
        self.review.streak = 1
        self.review.needs_review = False
        self.review.save()

        self.user.profile.on_vacation = True
        self.user.profile.save()

        reviews_affected = all_srs()
        self.assertEqual(reviews_affected, 0)

    def test_returning_review_count_that_is_time_delimited_functions_correctly(
        self
    ):
        new_review = create_review(create_vocab("arbitrary word"), self.user)
        new_review.needs_review = False
        more_than_24_hours_from_now = timezone.now() + timezone.timedelta(
            hours=25
        )
        new_review.next_review_date = more_than_24_hours_from_now
        new_review.save()
        self.review.next_review_date = timezone.now()
        self.review.needs_review = False
        self.review.save()

        future_reviews = get_users_future_reviews(
            self.user, time_limit=timezone.timedelta(hours=24)
        )

        self.assertEqual(future_reviews.count(), 1)

    def test_returning_future_review_count_with_invalid_time_limit_returns_empty_queryset(
        self
    ):
        self.review.next_review_date = timezone.now()
        self.review.needs_review = False
        self.review.save()

        future_reviews = get_users_future_reviews(
            self.user, time_limit=timezone.timedelta(hours=-1)
        )

        self.assertEqual(future_reviews.count(), 0)

    def test_returning_future_review_count_with_incorrect_argument_type_falls_back_to_default(
        self
    ):
        self.review.next_review_date = timezone.now()
        self.review.needs_review = False
        self.review.save()

        future_reviews = get_users_future_reviews(
            self.user, time_limit="this is not a timedelta"
        )

        self.assertGreater(future_reviews.count(), 0)

    def test_update_all_users_only_gets_active_users(self):
        user2 = create_user("sup")
        create_profile(user2, "any_key", 5)
        user2.profile.last_visit = past_time(24 * 6)
        self.user.profile.last_visit = past_time(24 * 8)
        user2.profile.save()
        self.user.profile.save()

        affected_count = sync_all_users_to_wk()
        self.assertEqual(affected_count, 1)

    @responses.activate
    def test_when_reading_level_changes_on_wanikani_we_catch_that_change_and_comply(
        self
    ):
        pass

    @responses.activate
    def test_when_wanikani_changes_meaning_no_duplicate_is_created(self):
        pass

    def test_when_user_resets_their_account_all_unlocked_levels_are_removed_except_current_wk_level(
        self
    ):
        self.user.profile.unlocked_levels.get_or_create(level=1)
        self.user.profile.unlocked_levels.get_or_create(level=2)
        self.user.profile.unlocked_levels.get_or_create(level=3)
        self.user.profile.unlocked_levels.get_or_create(level=4)
        self.user.refresh_from_db()
        self.assertListEqual(
            self.user.profile.unlocked_levels_list(), [5, 1, 2, 3, 4]
        )
        reset_levels(self.user, 1)
        self.user.refresh_from_db()
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [])

    @responses.activate
    def test_when_user_resets_their_account_we_remove_all_reviews_and_then_unlock_their_current_level(
        self
    ):
        return
        self.user.profile.unlocked_levels.get_or_create(level=1)
        new_review = create_review(create_vocab("arbitrary word"), self.user)
        new_review.needs_review = True
        new_review.save()
        self.assertEqual(get_users_current_reviews(self.user).count(), 2)

        # TODO Fill with V2 mocks.

        reset_user(self.user, 1)

        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(get_users_lessons(self.user).count(), 0)
        self.assertEqual(self.user.profile.level, 5)