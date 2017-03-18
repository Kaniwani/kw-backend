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

    def test_preprocessor_future_reviews_counts_correctly_provides_same_day_review_count(self):
        within_half_hour_review = create_review_for_specific_time(self.user, "some word",
                                                                  timezone.now() + timedelta(minutes=30))
        within_day_review = create_review_for_specific_time(self.user, "some word",
                                                            timezone.now() + timedelta(hours=12))
        after_a_day_review = create_review_for_specific_time(self.user, "some word",
                                                             timezone.now() + timedelta(hours=48))

        req = self.factory.get("/kw/")
        req.user = self.user

        context_data = review_count_preprocessor(req)

        self.assertEqual(context_data['reviews_within_day_count'], 2)
        self.assertEqual(context_data['reviews_within_hour_count'], 1)
        self.assertEqual(context_data['review_count'], 1)

    def test_future_review_counts_preprocessor_does_not_include_currently_active_reviews(self):
        within_day_review = create_review_for_specific_time(self.user, "some word",
                                                            timezone.now() + timedelta(hours=12))
        within_day_review.needs_review = True
        within_day_review.save()

        req = self.factory.get("/kw/")
        req.user = self.user

        context_data = review_count_preprocessor(req)

        self.assertEqual(context_data['reviews_within_day_count'], 0)
        self.assertEqual(context_data['reviews_within_hour_count'], 0)
        self.assertEqual(context_data['review_count'], 2)

    def test_review_count_preprocessor_returns_sane_values_when_user_has_no_vocabulary_unlocked(self):
        self.review.delete()
        req = self.factory.get("/kw/")
        req.user = self.user

        context_data = review_count_preprocessor(req)

        self.assertEqual(context_data['reviews_within_day_count'], 0)
        self.assertEqual(context_data['reviews_within_hour_count'], 0)
        self.assertEqual(context_data['review_count'], 0)
