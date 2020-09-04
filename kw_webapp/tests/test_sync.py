import re
from copy import deepcopy

import responses
import time
from django.test import TestCase
from django.utils import timezone

from api.sync.SyncerFactory import Syncer
from api.sync.WanikaniUserSyncerV2 import WanikaniUserSyncerV2
from kw_webapp import constants
from kw_webapp.models import Vocabulary, UserSpecific
from kw_webapp.srs import all_srs
from kw_webapp.tasks import (
    past_time,
    unlock_all_possible_levels_for_user,
    get_users_future_reviews,
    sync_all_users_to_wk,
    sync_with_wk,
    get_users_current_reviews, get_users_lessons,
)
from kw_webapp.tests.utils import (
    create_review,
    create_vocab,
    create_user,
    create_profile,
    create_reading,
    mock_assignments_with_one_assignment,
    mock_user_response_v2,
    mock_subjects_v2,
    mock_study_materials,
    create_lesson,
)


class TestSync(TestCase):
    def setUp(self):
        self.user = create_user("Tadgh")
        create_profile(self.user, "any_key", 5)
        self.prepLocalVocabulary()
        self.reading = create_reading(self.v, "ねこ", "猫", 1)
        self.review = create_review(self.v, self.user)
        self._vocab_api_regex = re.compile(
            r"https://www\.wanikani\.com/api/user/.*"
        )

    def prepLocalVocabulary(self):
        self.v = Vocabulary.objects.create()
        self.v.meaning = "radioactive bat"
        self.v.wk_subject_id = 1
        self.v.save()
        return self.v

    @responses.activate
    def test_unlock_all_unlocks_all(self):
        self.user.profile.api_valid = True
        self.user.profile.save()
        mock_assignments_with_one_assignment()

        checked_levels, unlocked_now_count, total_unlocked_count, locked_count = unlock_all_possible_levels_for_user(
            self.user
        )

        self.assertEqual(total_unlocked_count, 1)

    @responses.activate
    def test_syncing_vocabulary_pulls_srs_level_successfully(self):
        mock_user_response_v2()
        mock_assignments_with_one_assignment()
        mock_study_materials()

        Syncer.factory(self.user.profile).sync_with_wk()
        newly_synced_review = UserSpecific.objects.get(
            user=self.user, vocabulary__meaning=self.v.meaning
        )

        self.assertEqual(newly_synced_review.wanikani_srs_numeric, 4)

    def test_user_returns_from_vacation_correctly_increments_review_timestamps(
        self
    ):
        now = timezone.now()
        two_hours_ago = now - timezone.timedelta(hours=2)
        two_hours_from_now = now + timezone.timedelta(hours=2)
        four_hours_from_now = now + timezone.timedelta(hours=4)

        self.user.profile.on_vacation = True

        # Create review that should be reviewed never again, but got reviewed 2 hours ago.
        review = create_review(create_vocab("wazoop"), self.user)
        review.burned = True
        review.next_review_date = None
        review.last_studied = two_hours_ago
        review.save()

        self.user.profile.vacation_date = two_hours_ago
        self.user.profile.save()
        self.review.last_studied = two_hours_ago
        self.review.next_review_date = two_hours_from_now

        self.review.save()
        previously_studied = self.review.last_studied

        self.user.profile.return_from_vacation()
        all_srs(self.user)

        self.review.refresh_from_db()
        self.assertNotEqual(self.review.last_studied, previously_studied)

        self.assertAlmostEqual(
            self.review.next_review_date,
            four_hours_from_now,
            delta=timezone.timedelta(minutes=15),
        )
        self.assertAlmostEqual(
            self.review.last_studied, now, delta=timezone.timedelta(minutes=15)
        )
        self.assertAlmostEqual(
            review.last_studied,
            two_hours_ago,
            delta=timezone.timedelta(minutes=15),
        )
        self.assertAlmostEqual(review.next_review_date, None)

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
        self.review.streak = 1
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
    def test_creating_new_synonyms_for_users_who_arent_being_followed(self):
        # Mock synonyms response for V2.
        mock_user_response_v2()
        mock_subjects_v2()
        mock_assignments_with_one_assignment()
        mock_study_materials()
        # sync_unlocked_vocab_with_wk(self.user)
        self.user.profile.follow_me = False
        self.user.profile.save()

        sync_with_wk(self.user.id)

        synonyms_list = self.review.synonyms_list()
        self.assertIn("young girl", synonyms_list)
        self.assertIn("young lady", synonyms_list)
        self.assertIn("young miss", synonyms_list)

    @responses.activate
    def test_full_sync_of_user_on_v2(self):

        # Setup mocks for user response and full sync (with a single assignment)
        mock_user_response_v2()
        mock_assignments_with_one_assignment()
        mock_study_materials()
        mock_subjects_v2()

        self.user.profile.api_key_v2 = "whatever"
        self.user.profile.save()

        syncer = WanikaniUserSyncerV2(self.user.profile)
        syncer.sync_with_wk(full_sync=True)

        reviews = get_users_current_reviews(self.user)
        assert reviews.count() == 1

    @responses.activate
    def test_users_not_following_wanikani_still_get_vocab_unlocked_when_they_unlock_a_level(self):
        mock_user_response_v2()
        mock_assignments_with_one_assignment()
        mock_study_materials()
        mock_subjects_v2()

        self.user.profile.follow_me = False
        self.user.profile.api_key_v2 = "whatever"
        # Clear out all reviews so a level unlock works.
        UserSpecific.objects.filter(user=self.user).delete()
        syncer = WanikaniUserSyncerV2(self.user.profile)
        reviews = get_users_current_reviews(self.user)
        assert reviews.count() == 0
        new_review_count, unlocked_count, locked_count  = syncer.unlock_vocab(levels=[1])
        assert new_review_count == 1
        reviews = get_users_lessons(self.user)
        assert reviews.count() == 1

    @responses.activate
    def test_synonyms_are_ported_in_v2(self):
        mock_user_response_v2()
        mock_assignments_with_one_assignment()
        mock_study_materials()

        syncer = WanikaniUserSyncerV2(self.user.profile)
        syncer.sync_with_wk(full_sync=False)

        review = UserSpecific.objects.filter(user=self.user)[0]
        assert review.meaning_note is not None
        assert review.meaning_synonyms.count() == 3
        assert "young lady" in review.synonyms_list()

    @responses.activate
    def test_vocabulary_meaning_changes_carry_over(self):
        mock_subjects_v2()
        syncer = WanikaniUserSyncerV2(self.user.profile)
        assert self.v.meaning == "radioactive bat"
        updated_vocabulary_count = syncer.sync_top_level_vocabulary()
        assert updated_vocabulary_count == 1
        self.v.refresh_from_db()
        assert self.v.meaning == "One"

    @responses.activate
    def test_vocabulary_auxiliary_meanings_changes_carry_over(self):
        mock_subjects_v2()
        syncer = WanikaniUserSyncerV2(self.user.profile)
        assert self.v.auxiliary_meanings_whitelist is None
        updated_vocabulary_count = syncer.sync_top_level_vocabulary()
        assert updated_vocabulary_count == 1
        self.v.refresh_from_db()
        assert self.v.auxiliary_meanings_whitelist == "1,uno"

    @responses.activate
    def test_vocabulary_reading_changes_carry_over(self):
        mock_subjects_v2()
        syncer = WanikaniUserSyncerV2(self.user.profile)
        assert self.v.readings.count() == 1
        assert self.v.readings.all()[0].kana == "ねこ"
        updated_vocabulary_count = syncer.sync_top_level_vocabulary()
        assert updated_vocabulary_count == 1
        self.v.refresh_from_db()
        expected_reading_kanas = [
            reading.kana for reading in self.v.readings.all()
        ]
        expected_reading_kanjis = [
            reading.character for reading in self.v.readings.all()
        ]
        assert "いち" in expected_reading_kanas
        assert "一" in expected_reading_kanjis
        assert "one - but in japanese" in expected_reading_kanas

    @responses.activate
    def test_vocabulary_reading_deletions_occur(self):
        mock_subjects_v2()
        syncer = WanikaniUserSyncerV2(self.user.profile)
        assert self.v.readings.count() == 1
        assert self.v.readings.all()[0].kana == "ねこ"
        updated_vocabulary_count = syncer.sync_top_level_vocabulary()
        assert updated_vocabulary_count == 1
        self.v.refresh_from_db()
        stored_reading_kanas = [
            reading.kana for reading in self.v.readings.all()
        ]
        stored_reading_kanjis = [
            reading.character for reading in self.v.readings.all()
        ]

        assert "いち" in stored_reading_kanas
        assert "一" in stored_reading_kanjis
        assert "ねこ" not in stored_reading_kanas
        assert "one - but in japanese" in stored_reading_kanas

    def test_syncer_factory(self):
        # now for v2
        self.user.profile.api_key_v2 = "no longer empty!"
        self.user.profile.save()
        syncer = Syncer.factory(self.user.profile)
        assert isinstance(syncer, WanikaniUserSyncerV2)
