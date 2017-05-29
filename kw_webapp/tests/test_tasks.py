from copy import deepcopy

import responses
from django.test import TestCase
from django.utils import timezone
from kw_webapp import constants
from kw_webapp.models import Vocabulary, UserSpecific
from kw_webapp.tasks import create_new_vocabulary, past_time, all_srs, get_vocab_by_meaning, associate_vocab_to_user, \
    build_API_sync_string_for_user, sync_unlocked_vocab_with_wk, \
    lock_level_for_user, unlock_all_possible_levels_for_user, build_API_sync_string_for_user_for_levels, \
    user_returns_from_vacation, get_users_future_reviews, process_vocabulary_response_for_user, sync_all_users_to_wk, \
    get_vocab_by_kanji
from kw_webapp.tests import sample_api_responses
from kw_webapp.tests.sample_api_responses import single_vocab_requested_information
from kw_webapp.tests.utils import create_userspecific, create_vocab, create_user, create_profile, create_reading


class TestTasks(TestCase):
    def setUp(self):
        self.user = create_user("Tadgh")
        create_profile(self.user, "any_key", 5)
        self.vocabulary = create_vocab("radioactive bat")
        self.reading = create_reading(self.vocabulary, "ねこ", "猫", 2)
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
        self.user.profile.api_valid = True
        self.user.profile.save()
        resp_body = sample_api_responses.single_vocab_response
        level_list = [level for level in range(1, self.user.profile.level + 1)]
        responses.add(responses.GET, build_API_sync_string_for_user_for_levels(self.user, level_list),
                      json=resp_body,
                      status=200,
                      content_type='application/json')

        checked_levels, unlocked_now_count, total_unlocked_count,  locked_count = unlock_all_possible_levels_for_user(self.user)

        self.assertListEqual(level_list, checked_levels)
        self.assertEqual(total_unlocked_count, 1)

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
        an_hour_ago = now - timezone.timedelta(hours=1)
        two_hours_ago = now - timezone.timedelta(hours=2)
        two_hours_from_now = now + timezone.timedelta(hours=2)
        four_hours_from_now = now + timezone.timedelta(hours = 4)
        self.user.profile.vacation_date = two_hours_ago
        self.user.profile.save()
        self.review.last_studied = two_hours_ago
        self.review.next_review_date = two_hours_from_now

        self.review.save()
        previously_studied = self.review.last_studied

        user_returns_from_vacation(self.user)

        self.review.refresh_from_db()
        self.assertNotEqual(self.review.last_studied, previously_studied)

        self.assertAlmostEqual(self.review.next_review_date, four_hours_from_now, delta=timezone.timedelta(seconds=1))
        self.assertAlmostEqual(self.review.last_studied, now, delta=timezone.timedelta(seconds=1))

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

        #Mock response so that the level changes on our default vocab.
        responses.add(responses.GET, build_API_sync_string_for_user(self.user),
                      json=sample_api_responses.single_vocab_response,
                      status=200,
                      content_type='application/json')


        sync_unlocked_vocab_with_wk(self.user)

        vocabulary = get_vocab_by_meaning("radioactive bat")

        self.assertEqual(vocabulary.readings.count(), 1)



    @responses.activate
    def test_when_wanikani_changes_meaning_no_duplicate_is_created(self):
        resp_body = deepcopy(sample_api_responses.single_vocab_response)
        resp_body['requested_information'][0]['meaning'] = "NOT radioactive bat"

        #Mock response so that the level changes on our default vocab.
        responses.add(responses.GET, build_API_sync_string_for_user(self.user),
                      json=resp_body,
                      status=200,
                      content_type='application/json')

        sync_unlocked_vocab_with_wk(self.user)

        #Will fail if 2 vocab exist with same kanji.
        vocabulary = get_vocab_by_kanji("猫")

    def test_if_vocab_meaning_changes_on_aglomerated_vocab_it_is_correctly_split(self):
        original_vocabulary = create_vocab("construction")
        reading1 = create_reading(original_vocabulary, "ねこ", "工事", 2)
        reading2 = create_reading(original_vocabulary, "ねこ", "工作", 2)
        reading3 = create_reading(original_vocabulary, "ねこ", "建設", 2)
        original_review = create_userspecific(original_vocabulary, self.user)
        assert(len(original_vocabulary.readings.all()) == 3)

        # Now for kanji 工作, add handicraft to meanings, so that it should be split as meanings no longer identical
        # Construction -> 工事, 建設
        # Construction, handicraft -> 工作
        # Mock response so that the meaning is modified on the vocab with the aforementioned Kanji.
        responses.add(responses.GET, build_API_sync_string_for_user(self.user),
                      json=sample_api_responses.added_meaning_to_conglomerate_vocab_sample_response,
                      status=200,
                      content_type='application/json')

        sync_unlocked_vocab_with_wk(self.user)
        original_vocabulary.refresh_from_db()

        # We should have stripped the 工作 kanji from the vocabulary.
        assert(len(original_vocabulary.readings.all()) == 2)

        # That kanji should now be in it's own vocabulary, which has duplicated the SRS information of the
        # pre-split review.
        new_vocabulary = UserSpecific.objects.filter(user=self.user, vocabulary__meaning="construction, handicraft")
        assert(len(new_vocabulary.readings.all()) == 1)


        new_review = UserSpecific.objects.get(user=self.user, vocabulary=new_vocabulary)

        #Should have duplicated all KW srs information.
        assert(new_review.streak == original_review.streak)
        assert(new_review.correct == original_review.correct)
        assert(new_review.incorrect == original_review.incorrect)
        assert(new_review.notes == original_review.notes)
        assert(new_review.last_studied == original_review.last_studied)
        assert(new_review.needs_review == original_review.needs_review)
        assert(new_review.critial == original_review.critial)
        assert(new_review.hidden == original_review.hidden)

        # Any WK information is not duplicated, and is instead read from the API response.
        assert(new_review.wanikani_burned is True)
        assert(new_review.wanikani_srs_numeric == 9)
        assert(new_review.wanikani_srs == "burned")

        # NOTE: Think about Wanikani_burned attribute on UserSpecific. We don't want to duplicate this setting,
        # instead we want to check the API responses during Review clone time.



    def test_if_vocab_meaning_changes_and_it_now_matches_another_vocab_it_is_aglomerated(self):
        assert(len(self.user.reviews.all()) == 1)
        unique_vocabulary = create_vocab("radioactive bat, doggo.")
        create_reading(unique_vocabulary, "いぬ", "犬", 2)
        unique_review = create_userspecific(unique_vocabulary, self.user)
        # Lets set some higher SRS values here, so we can show that hte merger pick the higher of the two.
        higher_streak = unique_review.streak = 3
        higher_correct = unique_review.correct = 4
        higher_incorrect = unique_review.incorrect = 1
        unique_review.save()

        #Ensure that the user currently has two reviews.
        assert(len(self.user.reviews.all()) == 2)

        # Now for kanji 犬, remove doggo from meanings, leaving only radioactive bat, which should cause a merger.
        # What was originally
        # radioactive bat -> 猫
        # radioactive bat, doggo -> 犬

        # will become:

        # radioactive bat -> 犬, 猫

        responses.add(responses.GET, build_API_sync_string_for_user(self.user),
                      json=sample_api_responses.single_vocab_changed_meaning_and_should_now_merge,
                      status=200,
                      content_type='application/json')

        sync_unlocked_vocab_with_wk(self.user)
        unique_vocabulary.refresh_from_db()
        found_vocab = get_vocab_by_meaning("radioactive bat")
        assert(len(found_vocab.readings.all()) == 2)

        #Ensure that the user currently has one review, reflecting the merger. Essentially, make all the same checks
        # that we make in the one time script.
        assert(len(self.user.reviews.all()) == 1)
        only_review = self.user.reviews.first()
        assert(only_review.correct == higher_correct)
        assert(only_review.streak == higher_streak)
        assert(only_review.incorrect == higher_incorrect)
        assert(only_review.vocabulary.id == found_vocab.id)



    def test_one_time_script_for_vocabulary_merging_works(self):
        # Merger should:
        # 1) Pull entire Wanikani vocabulary set.
        # 2) For each vocabulary, check kanji.

        # Option A:
        # 3) If multiple vocab that have a reading with that kanji are returned, Create *one* new vocab for that kanji, with current info from API.
        # 3.5) Make sure to copy over the various metadata on the reading we have previously pulled (sentences etc)
        # 4) Find all Reviews that point to any of the previous vocabulary objects.
        # 5) find maximum of all the reviews. Which has highest SRS, etc. This will be the user's original vocab.
        # 6) Point the review's Vocabulary to the newly created vocabulary object from step 3.
        # 7) Delete all other Vocabulary that are now out of date. This should cascade deletion down to the other reviews.

        # Option B:
        # 3) If only one vocab is found for a particular kanji, we have successfully *not* created duplicates, meaning the WK vocab has never changed meaning.
        # 4) We do not have to do anything here. Woohoo!


