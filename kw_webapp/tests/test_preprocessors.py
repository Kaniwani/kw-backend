
from django.test import TestCase, RequestFactory, Client

from kw_webapp.tests.utils import create_user, create_profile, create_vocab, create_reading, create_userspecific


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
        from KW.preprocessors import srs_count_preprocessor
        req = self.factory.get('/kw/')
        req.user = self.user

        srs_count_dict = srs_count_preprocessor(req)

        self.assertEqual(srs_count_dict['srs_apprentice_count'], 1)
        self.assertEqual(srs_count_dict['srs_guru_count'], 0)
        self.assertEqual(srs_count_dict['srs_master_count'], 0)
        self.assertEqual(srs_count_dict['srs_enlightened_count'], 0)
        self.assertEqual(srs_count_dict['srs_burned_count'], 0)
