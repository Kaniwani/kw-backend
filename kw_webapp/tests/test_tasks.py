import re
from copy import deepcopy

import responses
import time
from django.test import TestCase
from django.utils import timezone
from kw_webapp import constants
from kw_webapp.models import Vocabulary, UserSpecific, MeaningSynonym, AnswerSynonym
from kw_webapp.tasks import create_new_vocabulary, past_time, all_srs, associate_vocab_to_user, \
    build_API_sync_string_for_user, sync_unlocked_vocab_with_wk, \
    lock_level_for_user, unlock_all_possible_levels_for_user, build_API_sync_string_for_user_for_levels, \
    user_returns_from_vacation, get_users_future_reviews, sync_all_users_to_wk, \
    reset_user, get_users_current_reviews, reset_levels, get_users_lessons, get_vocab_by_kanji, \
    build_user_information_api_string, get_level_pages
from kw_webapp.tests import sample_api_responses
from kw_webapp.tests.sample_api_responses import single_vocab_requested_information
from kw_webapp.tests.utils import create_userspecific, create_vocab, create_user, create_profile, create_reading, \
    create_review_for_specific_time, mock_vocab_list_response_with_single_vocabulary, mock_user_info_response
from kw_webapp.utils import generate_user_stats, one_time_merge_level


class TestTasks(TestCase):

    def setUp(self):
        self.user = create_user("Tadgh")
        create_profile(self.user, "any_key", 5)
        self.vocabulary = create_vocab("radioactive bat")
        self.reading = create_reading(self.vocabulary, "ねこ", "猫", 2)
        self.review = create_userspecific(self.vocabulary, self.user)
        self._vocab_api_regex = re.compile("https://www\.wanikani\.com/api/user/.*")

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

    def test_building_api_string_adds_correct_levels(self):
        self.user.profile.unlocked_levels.get_or_create(level=5)
        self.user.profile.unlocked_levels.get_or_create(level=3)
        self.user.profile.unlocked_levels.get_or_create(level=1)
        self.user.profile.save()

        api_call = build_API_sync_string_for_user(self.user)
        correct_string = "https://www.wanikani.com/api/user/any_key/vocabulary/5,3,1"

        self.assertEqual(correct_string, api_call)

    def test_locking_level_removes_all_reviews_at_that_level(self):
        self.vocabulary.readings.create(level=5, kana="猫", character="whatever")
        self.vocabulary.readings.create(level=5, kana="猫二", character="whatever2")

        lock_level_for_user(5, self.user)

        available_reviews = UserSpecific.objects.filter(user=self.user, vocabulary__readings__level=5).all()
        self.assertFalse(available_reviews)

    def test_locking_level_removes_level_from_unlocked_list(self):
        self.user.profile.unlocked_levels.get_or_create(level=7)
        self.user.profile.unlocked_levels.get_or_create(level=6)
        self.vocabulary.readings.create(level=6, kana="猫二", character="whatever2")

        lock_level_for_user(6, self.user)
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [5, 7])

    def test_create_new_vocab_based_on_json_works(self):
        vocab = create_new_vocabulary(single_vocab_requested_information)
        self.assertIsInstance(vocab, Vocabulary)

    @responses.activate
    def test_creating_new_synonyms_on_sync(self):
        resp_body = deepcopy(sample_api_responses.single_vocab_response)
        resp_body["requested_information"][0]["user_specific"]["user_synonyms"] = ["kitten", "large rat"]

        responses.add(responses.GET, self._vocab_api_regex,
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
        self.user.profile.api_valid = True
        self.user.profile.save()
        resp_body = sample_api_responses.single_vocab_response
        level_list = [level for level in range(1, self.user.profile.level + 1)]
        responses.add(responses.GET, self._vocab_api_regex,
                      json=resp_body,
                      status=200,
                      content_type='application/json')

        checked_levels, unlocked_now_count, total_unlocked_count, locked_count = unlock_all_possible_levels_for_user(
            self.user)

        self.assertListEqual(level_list, checked_levels)
        self.assertEqual(total_unlocked_count, 1)

    @responses.activate
    def test_syncing_vocabulary_pulls_srs_level_successfully(self):
        resp_body = sample_api_responses.single_vocab_response
        responses.add(responses.GET, self._vocab_api_regex,
                      json=resp_body,
                      status=200,
                      content_type='application/json')

        sync_unlocked_vocab_with_wk(self.user)
        newly_synced_review = UserSpecific.objects.get(user=self.user, vocabulary__meaning=self.vocabulary.meaning)

        self.assertEqual(newly_synced_review.wanikani_srs, "apprentice")
        self.assertEqual(newly_synced_review.wanikani_srs_numeric, 3)

    def test_user_returns_from_vacation_correctly_increments_review_timestamps(self):
        now = timezone.now()
        two_hours_ago = now - timezone.timedelta(hours=2)
        two_hours_from_now = now + timezone.timedelta(hours=2)
        four_hours_from_now = now + timezone.timedelta(hours=4)

        self.user.profile.on_vacation = True

        # Create review that should be reviewed never again, but got reviewed 2 hours ago.
        review = create_userspecific(create_vocab("wazoop"), self.user)
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

        self.assertAlmostEqual(self.review.next_review_date, four_hours_from_now, delta=timezone.timedelta(minutes=15))
        self.assertAlmostEqual(self.review.last_studied, now, delta=timezone.timedelta(minutes=15))
        self.assertAlmostEqual(review.last_studied, two_hours_ago, delta=timezone.timedelta(minutes=15))
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
        new_review = create_userspecific(create_vocab("arbitrary word"), self.user)
        new_review.needs_review = False
        more_than_24_hours_from_now = timezone.now() + timezone.timedelta(hours=25)
        new_review.next_review_date = more_than_24_hours_from_now
        new_review.save()
        self.review.next_review_date = timezone.now()
        self.review.needs_review = False
        self.review.save()

        future_reviews = get_users_future_reviews(self.user, time_limit=timezone.timedelta(hours=24))

        self.assertEqual(future_reviews.count(), 1)

    def test_returning_future_review_count_with_invalid_time_limit_returns_empty_queryset(self):
        self.review.next_review_date = timezone.now()
        self.review.needs_review = False
        self.review.save()

        future_reviews = get_users_future_reviews(self.user, time_limit=timezone.timedelta(hours=-1))

        self.assertEqual(future_reviews.count(), 0)

    def test_returning_future_review_count_with_incorrect_argument_type_falls_back_to_default(self):
        self.review.next_review_date = timezone.now()
        self.review.needs_review = False
        self.review.save()

        future_reviews = get_users_future_reviews(self.user, time_limit="this is not a timedelta")

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
    def test_when_reading_level_changes_on_wanikani_we_catch_that_change_and_comply(self):
        resp_body = sample_api_responses.single_vocab_response

        # Mock response so that the level changes on our default vocab.
        responses.add(responses.GET, self._vocab_api_regex,
                      json=sample_api_responses.single_vocab_response,
                      status=200,
                      content_type='application/json')

        sync_unlocked_vocab_with_wk(self.user)

        vocabulary = Vocabulary.objects.get(meaning="radioactive bat")

        self.assertEqual(vocabulary.readings.count(), 1)

    @responses.activate
    def test_when_wanikani_changes_meaning_no_duplicate_is_created(self):
        resp_body = deepcopy(sample_api_responses.single_vocab_response)
        resp_body['requested_information'][0]['meaning'] = "NOT radioactive bat"

        # Mock response so that the level changes on our default vocab.
        responses.add(responses.GET, build_API_sync_string_for_user_for_levels(self.user, [self.user.profile.level, ]),
                      json=resp_body,
                      status=200,
                      content_type='application/json')

        sync_unlocked_vocab_with_wk(self.user)

        # Will fail if 2 vocab exist with same kanji.
        vocabulary = get_vocab_by_kanji("猫")

    @responses.activate
    def test_one_time_script_for_vocabulary_merging_works(self):
        # Merger should:
        # 1) Pull entire Wanikani vocabulary set.
        # 2) For each vocabulary, check kanji.

        # Option A:

        # 3) If multiple vocab that have a reading with that kanji are returned, Create *one* new vocab for that kanji,
        #  with current info from API.

        # 3.5) Make sure to copy over the various metadata on the reading we have previously pulled (sentences etc)

        # 4) Find all Reviews that point to any of the previous vocabulary objects.

        # 5) Find maximum of all the reviews when grouped by user. Which has highest SRS, etc. This will be the user's
        # original vocab. Probably best to confirm by checking creation date.

        # 6) Point the review's Vocabulary to the newly created vocabulary object from step 3.

        # 7) Delete all other Vocabulary that are now out of date. This should cascade deletion
        # down to the other reviews.

        # Option B: 3) If only one vocab is found for a particular kanji, we have successfully *not* created
        # duplicates, meaning the WK vocab has never changed meaning. 4) We do not have to do anything here. Woohoo!

        # Create two vocab, identical kanji, different meanings.
        v1 = create_vocab("dog")  # < -- vestigial vocab.
        v2 = create_vocab("dog, woofer, pupper")  # < -- real, current vocab.
        create_reading(v1, "doggo1", "犬", 5)
        create_reading(v2, "doggo2", "犬", 5)

        # Make it so that review 1 has overall better SRS score for the user.
        review_1 = create_userspecific(v1, self.user)
        review_1.streak = 4
        review_1.correct = 4
        review_1.incorrect = 2
        review_1.save()

        review_2 = create_userspecific(v2, self.user)
        review_2.streak = 2
        review_2.correct = 4
        review_2.incorrect = 3
        review_2.save()

        MeaningSynonym.objects.create(review=review_1, text="flimflammer")
        MeaningSynonym.objects.create(review=review_2, text="shazwopper")
        AnswerSynonym.objects.create(review=review_1, character="CHS1", kana="KS1")
        AnswerSynonym.objects.create(review=review_2, character="CHS2", kana="KS2")

        # Assign another user an old version of the vocab.
        user2 = create_user("asdf")
        review_3 = create_userspecific(v1, user2)
        review_3.streak = 5
        review_3.correct = 5
        review_3.incorrect = 0
        review_3.save()

        # User now has two different vocab, each with their own meaning, however kanji are identical.

        # Pull fake "current" vocab. this response, wherein we fetch the data from WK, and it turns out we already
        # have a local vocabulary with an identical meaning (i.e., we have already stored the correct and
        # currently active vocabulary.
        responses.add(responses.GET,  "https://www.wanikani.com/api/user/{}/vocabulary/{}".format(constants.API_KEY, self.user.profile.level),
                      json=sample_api_responses.single_vocab_existing_meaning_and_should_now_merge,
                      status=200,
                      content_type='application/json')

        old_vocab = Vocabulary.objects.filter(readings__character="犬")
        self.assertEqual(old_vocab.count(), 2)

        generate_user_stats(self.user)
        one_time_merge_level(self.user.profile.level)
        generate_user_stats(self.user)

        new_vocab = Vocabulary.objects.filter(readings__character="犬")
        self.assertEqual(new_vocab.count(), 1)

        new_review = UserSpecific.objects.filter(user=self.user, vocabulary__readings__character="犬")
        self.assertEqual(new_review.count(), 1)
        new_review = new_review[0]
        self.assertEqual(new_review.streak, review_1.streak)
        self.assertEqual(new_review.correct, review_1.correct)
        self.assertEqual(new_review.incorrect, review_1.incorrect)
        self.assertEqual(new_review.next_review_date, review_1.next_review_date)
        self.assertEqual(new_review.last_studied, review_1.last_studied)

        # Should have smashed together all the synonyms too.
        self.assertEqual(len(new_review.synonyms_list()), 2)
        self.assertEqual(len(new_review.reading_synonyms.all()), 2)

        second_users_reviews = UserSpecific.objects.filter(user=user2)
        self.assertEqual(second_users_reviews.count(), 1)
        user_two_review = second_users_reviews[0]
        self.assertEqual(user_two_review.streak, 5)
        self.assertTrue(user_two_review.vocabulary.meaning == "dog, woofer, pupper")


    def test_when_user_resets_their_account_all_unlocked_levels_are_removed_except_current_wk_level(self):
        self.user.profile.unlocked_levels.get_or_create(level=1)
        self.user.profile.unlocked_levels.get_or_create(level=2)
        self.user.profile.unlocked_levels.get_or_create(level=3)
        self.user.profile.unlocked_levels.get_or_create(level=4)
        self.user.refresh_from_db()
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [5, 1, 2, 3, 4])
        reset_levels(self.user, 1)
        self.user.refresh_from_db()
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [])

    @responses.activate
    def test_when_user_resets_their_account_we_remove_all_reviews_and_then_unlock_their_current_level(self):
        self.user.profile.unlocked_levels.get_or_create(level=1)
        new_review = create_userspecific(create_vocab("arbitrary word"), self.user)
        new_review.needs_review = True
        new_review.save()
        self.assertEqual(get_users_current_reviews(self.user).count(), 2)

        mock_vocab_list_response_with_single_vocabulary(self.user)
        mock_user_info_response(self.user.profile.api_key)

        reset_user(self.user, 1)

        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(get_users_lessons(self.user).count(), 0)
        self.assertEqual(self.user.profile.level, 5)

