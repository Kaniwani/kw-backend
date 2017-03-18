from datetime import timedelta
from django.test import TestCase, RequestFactory, Client
from django.utils import timezone

from KW.preprocessors import review_count_preprocessor, srs_level_count_preprocessor
from kw_webapp.tests.utils import create_user, create_profile, create_vocab, create_reading, create_userspecific, \
    create_review_for_specific_time


class TestPreprocessors(TestCase):
    def setUp(self):
        self.user = create_user("user1")
        self.user.set_password("password")
        self.user.save()
        create_profile(self.user, "some_key", 5)
        # create a piece of vocab with one reading.
        self.vocabulary = create_vocab("cat")
        self.cat_reading = create_reading(self.vocabulary, "kana", "kanji", 5)

        self.review = create_userspecific(self.vocabulary, self.user)
        self.factory = RequestFactory()

    def test_preprocessor_srs_counts_are_correct(self):
        req = self.factory.get('/kw/')
        req.user = self.user

        srs_count_dict = srs_level_count_preprocessor(req)

        self.assertEqual(srs_count_dict['srs_apprentice_count'], 1)
        self.assertEqual(srs_count_dict['srs_guru_count'], 0)
        self.assertEqual(srs_count_dict['srs_master_count'], 0)
        self.assertEqual(srs_count_dict['srs_enlightened_count'], 0)
        self.assertEqual(srs_count_dict['srs_burned_count'], 0)




