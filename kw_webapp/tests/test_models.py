from itertools import chain

from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.test import Client, TestCase

from kw_webapp import constants
from kw_webapp.models import MeaningSynonym, UserSpecific, Profile
from kw_webapp.tests.utils import create_user, create_userspecific, create_reading, create_profile
from kw_webapp.tests.utils import create_vocab


class TestModels(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user("Tadgh")
        self.user.set_password("password")
        create_profile(self.user, "any key", 1)
        self.user.save()
        self.vocabulary = create_vocab("cat")
        self.review = create_userspecific(self.vocabulary, self.user)
        self.review.meaningsynonym_set.get_or_create(text="minou")

        # default state of a test is a user that has a single review, and the review has a single synonym added.

    def test_toggling_review_hidden_ownershp_fails_on_wrong_user(self):
        user2 = create_user("eve")
        user2.set_password("im_a_hacker")
        create_profile(user2, "any_key", 1)
        user2.save()
        relevant_review_id = UserSpecific.objects.get(user=self.user, vocabulary=self.vocabulary).id
        if self.client.login(username="eve", password="im_a_hacker"):
            response = self.client.post(path="/kw/togglevocab/", data={"review_id": relevant_review_id})
            self.assertIsInstance(response, HttpResponseForbidden)

    def test_toggling_review_hidden_ownership_works(self):
        relevant_review_id = UserSpecific.objects.get(user=self.user, vocabulary=self.vocabulary).id
        before_toggle_hidden = UserSpecific.objects.get(id=relevant_review_id).hidden

        if self.client.login(username=self.user.username, password="password"):
            response = self.client.post(path="/kw/togglevocab/", data={"review_id": relevant_review_id})
            print(response.content)
        else:
            self.fail("Couldn't log in!?")

        after_toggle_hidden = UserSpecific.objects.get(id=relevant_review_id)
        self.assertNotEqual(before_toggle_hidden, after_toggle_hidden)

    def test_adding_synonym_works(self):
        self.review.meaningsynonym_set.get_or_create(text="une petite chatte")
        self.assertEqual(2, len(self.review.meaningsynonym_set.all()))

    def test_removing_synonym_by_lookup_works(self):
        remove_text = "minou"
        self.review.remove_synonym(remove_text)
        self.assertNotIn(remove_text, self.review.synonyms_list())

    def test_removing_nonexistent_synonym_fails(self):
        remove_text = "un chien"
        self.assertRaises(MeaningSynonym.DoesNotExist, self.review.remove_synonym, remove_text)

    def test_removing_synonym_by_object_works(self):
        synonym, created = self.review.meaningsynonym_set.get_or_create(text="minou")
        self.review.meaningsynonym_set.remove(synonym)

    def test_reading_clean_fails_with_invalid_levels_too_high(self):
        v = create_vocab("cat")
        r = create_reading(v, "ねこ", "ねこ", 61)

        self.assertRaises(ValidationError, r.clean_fields)

    def test_reading_clean_fails_with_invalid_levels_too_low(self):
        v = create_vocab("cat")
        r = create_reading(v, "ねこ", "ねこ", 0)

        self.assertRaises(ValidationError, r.clean_fields)

    def test_vocab_number_readings_is_correct(self):
        r = create_reading(self.vocabulary, "ねこ", "ねこ", 2)
        r = create_reading(self.vocabulary, "ねこな", "猫", 1)
        self.assertEqual(self.vocabulary.reading_count(), 2)

    def test_available_readings_returns_only_readings_youve_unlocked(self):
        v = create_vocab("cat")
        r = create_reading(v, "ねこ", "ねこ", 5)
        r = create_reading(v, "ねこな", "猫", 1)

        self.assertTrue(len(v.available_readings(2)) == 1)

    def test_synonym_adding(self):
        review = create_userspecific(self.vocabulary, self.user)

        review.meaningsynonym_set.get_or_create(text="kitty")

        self.assertIn("kitty", review.synonyms_string())

    def test_get_all_readings_returns_original_and_added_readings(self):
        self.vocabulary.reading_set.create(kana="what", character="ars", level=5)
        review = create_userspecific(self.vocabulary, self.user)
        review.answersynonym_set.create(kana="shwoop", character="fwoop")

        expected = list(chain(self.vocabulary.reading_set.all(), review.answersynonym_set.all()))

        self.assertListEqual(expected, review.get_all_readings())

    def test_setting_twitter_account_correctly_prepends_at_symbol(self):
        non_prepended_account_name = "Tadgh"
        self.user.profile.set_twitter_account(non_prepended_account_name)

        users_profile = Profile.objects.get(user=self.user)
        self.assertEqual(users_profile.twitter, "@Tadgh")

    def test_setting_twitter_account_works_when_input_is_already_valid(self):
        account_name = "@Tadgh"
        self.user.profile.set_twitter_account(account_name)

        users_profile = Profile.objects.get(user=self.user)

        self.assertEqual(users_profile.twitter, "@Tadgh")

    def test_setting_an_invalid_twitter_handle_does_not_modify_model_instance(self):
        invalid_account_name = "!!"
        old_twitter = self.user.profile.twitter

        self.user.profile.set_twitter_account(invalid_account_name)

        users_profile = Profile.objects.get(user=self.user)

        self.assertEqual(users_profile.twitter, old_twitter)

    def test_setting_a_blank_twitter_handle_does_not_modify_model_instance(self):
        invalid_account_name = "@"
        old_twitter = self.user.profile.twitter

        self.user.profile.set_twitter_account(invalid_account_name)

        users_profile = Profile.objects.get(user=self.user)

        self.assertEqual(users_profile.twitter, old_twitter)

    def test_setting_valid_profile_website_modifies_model(self):
        valid_site = "www.kaniwani.com"

        self.user.profile.set_website(valid_site)

        users_profile = Profile.objects.get(user=self.user)

        self.assertEqual(users_profile.website, valid_site)

    def test_setting_website_with_http_prepended_gets_it_stripped(self):
        http_prepended_valid_site = "http://https://www.kaniwani.com"

        self.user.profile.set_website(http_prepended_valid_site)

        users_profile = Profile.objects.get(user=self.user)

        self.assertEqual(users_profile.website, "www.kaniwani.com")

    def test_protocol_only_strings_are_rejected_when_setting_website(self):
        invalid_url = "http://"
        old_url = self.user.profile.website

        self.user.profile.set_website(invalid_url)

        users_profile = Profile.objects.get(user=self.user)
        self.assertEqual(users_profile.website, old_url)

    def test_website_setting_on_None_site(self):
        invalid_url = None
        old_url = self.user.profile.website

        self.user.profile.set_website(invalid_url)

        users_profile = Profile.objects.get(user=self.user)
        self.assertEqual(users_profile.website, old_url)

    def test_setting_twitter_on_none_twitter(self):
        twitter_handle = None
        old_twitter = self.user.profile.twitter

        self.user.profile.set_twitter_account(twitter_handle)

        users_profile = Profile.objects.get(user=self.user)
        self.assertEqual(old_twitter, users_profile.twitter)

    def test_rounding_a_review_time_only_goes_up(self):
        self.review.next_review_date = self.review.next_review_date.replace(minute=17)
        self.review._round_review_time_up()
        self.review.refresh_from_db()

        self.assertEqual(self.review.next_review_date.minute % (constants.REVIEW_ROUNDING_TIME.total_seconds() / 60), 0)
        self.assertEqual(self.review.next_review_date.hour % (constants.REVIEW_ROUNDING_TIME.total_seconds() / (60 * 60)), 0)
        self.assertEqual(self.review.next_review_date.second % constants.REVIEW_ROUNDING_TIME.total_seconds(), 0)

    def test_default_review_times_are_not_rounded(self):
        rounded_time = self.review.next_review_date
        new_vocab = create_userspecific(create_vocab("fresh"), self.user)

        self.assertNotEqual(rounded_time, new_vocab.next_review_date)


    def test_handle_wanikani_level_up_correctly_levels_up(self):
        old_level = self.user.profile.level

        self.user.profile.handle_wanikani_level_change(self.user.profile.level + 1)
        self.user.refresh_from_db()

        self.assertEqual(self.user.profile.level, old_level + 1)


    def test_handle_wanikani_level_down_correctly_deletes_invalid_reviews(self):
        self.user.profile.level = 5
        self.user.profile.save()
        self.user.profile.unlocked_levels.get_or_create(level=5)

        #Create a review at current level
        vocab = create_vocab("ANY WORD")
        create_reading(vocab, "some reading", "some char", self.user.profile.level)
        create_userspecific(vocab, self.user)

        self.user.profile.handle_wanikani_level_change(self.user.profile.level - 1)

        reviews = UserSpecific.objects.filter(user=self.user)

        self.assertTrue(reviews.count() == 1)


    def test_handle_wanikani_level_down_correctly_removes_invalid_levels(self):
        self.user.profile.level = 5
        self.user.profile.save()
        self.user.profile.unlocked_levels.get_or_create(level=5)
        old_level = self.user.profile.level
        self.user.profile.handle_wanikani_level_change(old_level - 1)

        self.user.refresh_from_db()
        unlocked_levels = self.user.profile.unlocked_levels_list()

        self.assertTrue(old_level not in unlocked_levels)

