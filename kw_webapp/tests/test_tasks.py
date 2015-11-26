from django.test import TestCase, RequestFactory

from kw_webapp.models import Vocabulary, UserSpecific
from kw_webapp.tasks import create_new_vocabulary, past_time, all_srs, get_vocab_by_meaning, associate_vocab_to_user, \
    build_API_sync_string_for_user
from kw_webapp.tests.utils import create_userspecific, create_vocab, create_user, create_profile


class TestCeleryTasks(TestCase):
    def setUp(self):
        self.user = create_user("Tadgh")
        self.vocabulary = create_vocab("cat")
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
        found_vocab = get_vocab_by_meaning("cat")
        self.assertEqual(vocab_id, found_vocab.id)

    def test_get_vocab_by_meaning_raises_error_on_unknown_meaning(self):
        self.assertRaises(Vocabulary.DoesNotExist, get_vocab_by_meaning, "dog!")

    def test_associate_vocab_to_user_successfully_creates_review(self):
        review = associate_vocab_to_user(self.vocabulary, self.user)
        self.assertTrue(review.needs_review is True)

    def test_building_api_string_adds_correct_levels(self):
        p = create_profile(self.user, "any_api_key", 5)
        p.unlocked_levels.create(level=5)
        p.unlocked_levels.create(level=3)
        p.unlocked_levels.create(level=1)
        p.save()

        api_call = build_API_sync_string_for_user(self.user)
        correct_string = "https://www.wanikani.com/api/user/any_api_key/vocabulary/5,3,"

        self.assertEqual(correct_string, api_call)

    def test_create_new_vocab_based_on_json_works(self):
        vocab_json = {"character": "bleh", "kana": "bleh", "meaning": "two", "level": 1,
                      "user_specific": {"srs": "burned", "srs_numeric": 9, "unlocked_date": 1382674360,
                                        "available_date": 1398364200, "burned": True, "burned_date": 1398364287,
                                        "meaning_correct": 8, "meaning_incorrect": 0, "meaning_max_streak": 8,
                                        "meaning_current_streak": 8, "reading_correct": 8, "reading_incorrect": 0,
                                        "reading_max_streak": 8, "reading_current_streak": 8, "meaning_note": None,
                                        "user_synonyms": None, "reading_note": None}}
        vocab = create_new_vocabulary(vocab_json)
        self.assertIsInstance(vocab, Vocabulary)
