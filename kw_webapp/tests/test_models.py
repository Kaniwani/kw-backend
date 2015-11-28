from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.test import Client, TestCase

from kw_webapp.models import Synonym, UserSpecific
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
        self.review.synonym_set.get_or_create(text="minou")

        #default state of a test is a user that has a single review, and the review has a single synonym added.

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
        self.review.synonym_set.get_or_create(text="une petite chatte")
        self.assertEqual(2, len(self.review.synonym_set.all()))

    def test_removing_synonym_by_lookup_works(self):
        remove_text = "minou"
        self.review.remove_synonym(remove_text)
        self.assertNotIn(remove_text, self.review.synonyms_list())

    def test_removing_nonexistent_synonym_fails(self):
        remove_text = "un chien"
        self.assertRaises(Synonym.DoesNotExist, self.review.remove_synonym, remove_text)

    def test_removing_synonym_by_object_works(self):
        synonym, created = self.review.synonym_set.get_or_create(text="minou")
        self.review.synonym_set.remove(synonym)

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

        review.synonym_set.get_or_create(text="kitty")

        self.assertIn("kitty", review.synonyms_string())
