import re
from copy import deepcopy

import responses
import time
from django.test import TestCase
from django.utils import timezone

from api.sync.SyncerFactory import Syncer
from api.sync.WanikaniUserSyncer import WanikaniUserSyncer
from api.sync.WanikaniUserSyncerV1 import WanikaniUserSyncerV1
from api.sync.WanikaniUserSyncerV2 import WanikaniUserSyncerV2
from kw_webapp import constants
from kw_webapp.models import Vocabulary, UserSpecific, MeaningSynonym, AnswerSynonym
from kw_webapp.tasks import (
    sync_user_profile_with_wk)
from kw_webapp.tasks import past_time, all_srs, \
    sync_unlocked_vocab_with_wk, \
    unlock_all_possible_levels_for_user, build_API_sync_string_for_user_for_levels, \
    user_returns_from_vacation, get_users_future_reviews, sync_all_users_to_wk, \
    reset_user, get_users_current_reviews, reset_levels, get_users_lessons, get_vocab_by_kanji, \
    build_user_information_api_string, get_level_pages, sync_with_wk
from kw_webapp.tests import sample_api_responses
from kw_webapp.tests.sample_api_responses import single_vocab_requested_information
from kw_webapp.tests.utils import (
    create_review,
    create_vocab,
    create_user,
    create_profile,
    create_reading,
    create_review_for_specific_time,
    mock_vocab_list_response_with_single_vocabulary,
    mock_user_info_response,
    mock_assignments_with_one_assignment, mock_user_response_v2, mock_subjects_v2, mock_study_materials)
from kw_webapp.utils import generate_user_stats, one_time_merge_level


class TestTasks(TestCase):
    def setUp(self):
        self.user = create_user("Tadgh")
        create_profile(self.user, "any_key", 5)
        self.prepLocalVocabulary()

    def prepLocalVocabulary(self):
        self.v = Vocabulary.objects.create()
        self.v.meaning = "Test"
        self.v.wk_subject_id = 1
        self.reading = create_reading(self.v, "reading", "character", 1)
        self.v.save()
        return self.v

    @responses.activate
    def test_creating_new_synonyms_on_sync(self):
        resp_body = deepcopy(sample_api_responses.single_vocab_response)
        resp_body["requested_information"][0]["user_specific"]["user_synonyms"] = [
            "kitten",
            "large rat",
        ]

        responses.add(
            responses.GET,
            self._vocab_api_regex,
            json=resp_body,
            status=200,
            content_type="application/json",
        )

        sync_unlocked_vocab_with_wk(self.user)

        synonyms_list = self.review.synonyms_list()
        self.assertIn("large rat", synonyms_list)
        self.assertIn("kitten", synonyms_list)

    def test_building_unlock_all_string_works(self):
        sample_level = constants.LEVEL_MAX
        api_string = build_API_sync_string_for_user_for_levels(
            self.user, [level for level in range(1, sample_level + 1)]
        )

        expected = ",".join([str(level) for level in range(1, sample_level + 1)])

        self.assertTrue(expected in api_string)

    @responses.activate
    def test_unlock_all_unlocks_all(self):
        self.user.profile.api_valid = True
        self.user.profile.save()
        resp_body = sample_api_responses.single_vocab_response
        level_list = [level for level in range(1, self.user.profile.level + 1)]
        responses.add(
            responses.GET,
            self._vocab_api_regex,
            json=resp_body,
            status=200,
            content_type="application/json",
        )

        checked_levels, unlocked_now_count, total_unlocked_count, locked_count = unlock_all_possible_levels_for_user(
            self.user
        )

        self.assertListEqual(level_list, checked_levels)
        self.assertEqual(total_unlocked_count, 1)

    @responses.activate
    def test_syncing_vocabulary_pulls_srs_level_successfully(self):
        resp_body = sample_api_responses.single_vocab_response
        responses.add(
            responses.GET,
            self._vocab_api_regex,
            json=resp_body,
            status=200,
            content_type="application/json",
        )

        sync_unlocked_vocab_with_wk(self.user)
        newly_synced_review = UserSpecific.objects.get(
            user=self.user, vocabulary__meaning=self.vocabulary.meaning
        )

        self.assertEqual(newly_synced_review.wanikani_srs, "apprentice")
        self.assertEqual(newly_synced_review.wanikani_srs_numeric, 3)

    def test_user_returns_from_vacation_correctly_increments_review_timestamps(self):
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

        user_returns_from_vacation(self.user)

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
            review.last_studied, two_hours_ago, delta=timezone.timedelta(minutes=15)
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

    def test_returning_review_count_that_is_time_delimited_functions_correctly(self):
        new_review = create_review(create_vocab("arbitrary word"), self.user)
        new_review.needs_review = False
        more_than_24_hours_from_now = timezone.now() + timezone.timedelta(hours=25)
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
    def test_creating_new_synonyms_for_users_who_arent_being_followed(self):
        resp_body = deepcopy(sample_api_responses.single_vocab_response)
        resp_body["requested_information"][0]["user_specific"]["user_synonyms"] = ["kitten", "large rat"]

        responses.add(responses.GET, self._vocab_api_regex,
                      json=resp_body,
                      status=200,
                      content_type='application/json')

        #sync_unlocked_vocab_with_wk(self.user)
        self.user.profile.follow_me = False
        self.user.profile.save()

        sync_with_wk(self.user.id)

        synonyms_list = self.review.synonyms_list()
        self.assertIn("kitten", synonyms_list)
        self.assertIn("large rat", synonyms_list)

    def test_syncing_user_profile_on_v2(self):
        self.user.profile.api_key_v2 = "2510f001-fe9e-414c-ba19-ccf79af40060"
        self.user.profile.save()

        sync_user_profile_with_wk(self.user)

    @responses.activate
    def test_full_sync_of_user_on_v2(self):

        # Setup mocks for user response and full sync (with a single assignment)
        mock_user_response_v2()
        mock_assignments_with_one_assignment()
        mock_subjects_v2()

        self.user.profile.api_key_v2 = "whatever"
        self.user.profile.save()

        syncer = WanikaniUserSyncerV2(self.user.profile)
        syncer.sync_with_wk(full_sync=True)

        lessons = get_users_lessons(self.user)
        assert lessons.count() == 1


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
        assert self.v.meaning == "Test"
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
        assert self.v.readings.all()[0].kana == "reading"
        updated_vocabulary_count = syncer.sync_top_level_vocabulary()
        assert updated_vocabulary_count == 1
        self.v.refresh_from_db()
        expected_reading_kanas = [reading.kana for reading in self.v.readings.all()]
        assert "いち" in expected_reading_kanas
        assert "one - but in japanese" in expected_reading_kanas

    def test_syncer_factory(self):
        # Should return a V2 syncer when the user has a v2 api key added,
        # otherwise, V1.
        syncer = Syncer.factory(self.user.profile)
        assert isinstance(syncer, WanikaniUserSyncerV1)

        # now for v2
        self.user.profile.api_key_v2 = "no longer empty!"
        self.user.profile.save()
        syncer = Syncer.factory(self.user.profile)
        assert isinstance(syncer, WanikaniUserSyncerV2)
