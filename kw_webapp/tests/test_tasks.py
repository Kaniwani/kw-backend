from copy import deepcopy
from datetime import timedelta

import responses
from django.test import TestCase
from django.utils import timezone

from kw_webapp import constants
from kw_webapp.models import Vocabulary, UserSpecific
from kw_webapp.tasks import create_new_vocabulary, past_time, all_srs, get_vocab_by_meaning, associate_vocab_to_user, \
    build_API_sync_string_for_user, sync_unlocked_vocab_with_wk, \
    lock_level_for_user, unlock_all_possible_levels_for_user, build_API_sync_string_for_user_for_levels, \
    user_returns_from_vacation, get_users_future_reviews
from kw_webapp.tests import sample_api_responses
from kw_webapp.tests.sample_api_responses import single_vocab_requested_information
from kw_webapp.tests.utils import create_userspecific, create_vocab, create_user, create_profile


class TestTasks(TestCase):
    def setUp(self):
        self.user = create_user("Tadgh")
        create_profile(self.user, "any_key", 5)
        self.vocabulary = create_vocab("radioactive bat")
        self.review = create_userspecific(self.vocabulary, self.user)

    def test_userspecifics_needing_review_are_flagged(self):
        self.review.needs_review = False
        self.review.last_studied = past_time(5)
        self.review.save()
        all_srs()
        review = UserSpecific.objects.get(pk=self.review.id)
        self.assertTrue(review.needs_review)

    def test_get_vocab_by_meaning_gets_correct_vocab(self):
        vocab_id = self.vocabulary.id
        found_vocab = get_vocab_by_meaning("radioactive bat")
        self.assertEqual(vocab_id, found_vocab.id)

    def test_get_vocab_by_meaning_raises_error_on_unknown_meaning(self):
        self.assertRaises(Vocabulary.DoesNotExist, get_vocab_by_meaning, "dog!")

    def test_associate_vocab_to_user_successfully_creates_review(self):
        new_vocab = create_vocab("dishwasher")

        review, created = associate_vocab_to_user(new_vocab, self.user)

        self.assertTrue(review.needs_review is True)
        self.assertTrue(created)

    def test_building_api_string_adds_correct_levels(self):
        self.user.profile.unlocked_levels.get_or_create(level=5)
        self.user.profile.unlocked_levels.get_or_create(level=3)
        self.user.profile.unlocked_levels.get_or_create(level=1)
        self.user.profile.save()

        api_call = build_API_sync_string_for_user(self.user)
        correct_string = "https://www.wanikani.com/api/user/any_key/vocabulary/5,3,1,"

        self.assertEqual(correct_string, api_call)

    def test_locking_level_removes_all_reviews_at_that_level(self):
        self.vocabulary.reading_set.create(level=5, kana="猫", character="whatever")
        self.vocabulary.reading_set.create(level=5, kana="猫二", character="whatever2")

        lock_level_for_user(5, self.user)

        available_reviews = UserSpecific.objects.filter(user=self.user, vocabulary__reading__level=5).all()
        self.assertFalse(available_reviews)

    def test_locking_level_removes_level_from_unlocked_list(self):
        self.user.profile.unlocked_levels.get_or_create(level=7)
        self.user.profile.unlocked_levels.get_or_create(level=6)
        self.vocabulary.reading_set.create(level=6, kana="猫二", character="whatever2")

        lock_level_for_user(6, self.user)
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [5, 7])

    def test_create_new_vocab_based_on_json_works(self):

        vocab = create_new_vocabulary(single_vocab_requested_information)
        self.assertIsInstance(vocab, Vocabulary)

    @responses.activate
    def test_creating_new_synonyms_on_sync(self):
        resp_body = deepcopy(sample_api_responses.single_vocab_response)
        resp_body["requested_information"][0]["user_specific"]["user_synonyms"] = ["kitten", "large rat"]
        responses.add(responses.GET, build_API_sync_string_for_user(self.user),
                      json=resp_body,
                      status=200,
                      content_type='application/json')

        sync_unlocked_vocab_with_wk(self.user)
        self.assertListEqual(self.review.synonyms_list(), ["kitten", "large rat"])

    def test_building_unlock_all_string_works(self):
        sample_level = constants.LEVEL_MAX
        api_string = build_API_sync_string_for_user_for_levels(self.user,
                                                               [level for level in range(1, sample_level + 1)])

        expected = ",".join([str(level) for level in range(1, sample_level + 1)])

        self.assertTrue(expected in api_string)

    @responses.activate
    def test_unlock_all_unlocks_all(self):
        resp_body = sample_api_responses.single_vocab_response
        level_list = [level for level in range(1, self.user.profile.level + 1)]
        responses.add(responses.GET, build_API_sync_string_for_user_for_levels(self.user, level_list),
                      json=resp_body,
                      status=200,
                      content_type='application/json')

        checked_levels, unlocked_count, locked_count = unlock_all_possible_levels_for_user(self.user)

        self.assertListEqual(level_list, checked_levels)
        self.assertEqual(unlocked_count, 1)

    @responses.activate
    def test_syncing_vocabulary_pulls_srs_level_successfully(self):
        resp_body = sample_api_responses.single_vocab_response
        responses.add(responses.GET, build_API_sync_string_for_user(self.user),
                      json=resp_body,
                      status=200,
                      content_type='application/json')

        sync_unlocked_vocab_with_wk(self.user)
        newly_synced_review = UserSpecific.objects.get(user=self.user, vocabulary__meaning=self.vocabulary.meaning)

        self.assertEqual(newly_synced_review.wanikani_srs, "apprentice")
        self.assertEqual(newly_synced_review.wanikani_srs_numeric, 3)

    def test_user_returns_from_vacation_correctly_increments_review_timestamps(self):
        self.user.profile.on_vacation = True

        now = timezone.now()
        an_hour_ago = now - timedelta(hours=1)
        two_hours_ago = now - timedelta(hours=2)

        self.user.profile.vacation_date = an_hour_ago
        self.user.profile.save()
        self.review.last_studied = two_hours_ago
        self.review.save()
        previously_studied = self.review.last_studied

        user_returns_from_vacation(self.user)
        self.review.refresh_from_db()

        self.assertNotEqual(self.review.last_studied, previously_studied)
        self.assertAlmostEqual(self.review.last_studied, an_hour_ago, delta=timedelta(seconds=1))


    def test_returning_review_count_that_is_time_delimited_functions_correctly(self):
        new_review = create_userspecific(create_vocab("arbitrary word"), self.user)
        new_review.needs_review = False
        more_than_24_hours_from_now = timezone.now() + timedelta(hours=25)
        new_review.next_review_date = more_than_24_hours_from_now
        new_review.save()
        self.review.next_review_date = timezone.now()
        self.review.needs_review = False
        self.review.save()

        future_reviews = get_users_future_reviews(self.user, time_limit=timedelta(hours=24))

        self.assertEqual(future_reviews.count(), 1)

    def test_returning_future_review_count_with_invalid_time_limit_returns_empty_queryset(self):
        self.review.next_review_date = timezone.now()
        self.review.needs_review = False
        self.review.save()

        future_reviews = get_users_future_reviews(self.user, time_limit=timedelta(hours=-1))

        self.assertEqual(future_reviews.count(), 0)

    def test_returning_future_review_count_with_incorrect_argument_type_falls_back_to_default(self):
        self.review.next_review_date = timezone.now()
        self.review.needs_review = False
        self.review.save()

        future_reviews = get_users_future_reviews(self.user, time_limit="this is not a timedelta")

        self.assertGreater(future_reviews.count(), 0)



