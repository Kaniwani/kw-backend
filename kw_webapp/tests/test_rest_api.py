from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.tests.utils import create_user, create_profile, create_vocab, create_reading, create_userspecific


class TestPreprocessors(APITestCase):
    def setUp(self):
        self.user = create_user("Tadgh")
        create_profile(self.user, "any_key", 5)
        self.vocabulary = create_vocab("radioactive bat")
        self.reading = create_reading(self.vocabulary, "ねこ", "猫", 2)
        self.review = create_userspecific(self.vocabulary, self.user)

    def test_preprocessor_srs_counts_are_correct(self):
        self.client.force_login(user=self.user)
        self.review.answered_correctly(True)
        self.review.save()

        response = self.client.get(reverse("api:user-me"))
        abd = response.data.keys()
        self.assertEqual(response.data['profile']['reviews_within_hour_count'], 0)
        self.assertEqual(response.data['profile']['reviews_within_day_count'], 1)
