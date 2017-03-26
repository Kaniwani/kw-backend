import json
from datetime import timedelta

from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from KW.preprocessors import review_count_preprocessor
from kw_webapp.tests.utils import create_user, create_profile, create_vocab, create_reading, create_userspecific, \
    create_review_for_specific_time


class TestPreprocessors(APITestCase):
    def setUp(self):
        self.user = create_user("Tadgh")
        create_profile(self.user, "any_key", 5)
        self.vocabulary = create_vocab("radioactive bat")
        self.reading = create_reading(self.vocabulary, "ねこ", "猫", 2)
        self.review = create_userspecific(self.vocabulary, self.user)

    def test_profile_contains_correct_within_day_or_hour_counts(self):
        self.client.force_login(user=self.user)
        self.review.answered_correctly(True)
        self.review.save()

        response = self.client.get(reverse("api:user-me"))
        self.assertEqual(response.data['profile']['reviews_within_hour_count'], 0)
        self.assertEqual(response.data['profile']['reviews_within_day_count'], 1)

    def test_preprocessor_future_reviews_counts_correctly_provides_same_day_review_count(self):
        create_review_for_specific_time(self.user, "some word", timezone.now() + timedelta(minutes=30))
        create_review_for_specific_time(self.user, "some word", timezone.now() + timedelta(hours=12))
        create_review_for_specific_time(self.user, "some word", timezone.now() + timedelta(hours=48))

        self.client.force_login(user=self.user)
        response = self.client.get(reverse("api:user-me"))

        self.assertEqual(response.data["profile"]['reviews_within_day_count'], 2)
        self.assertEqual(response.data["profile"]['reviews_within_hour_count'], 1)
        self.assertEqual(response.data["profile"]['reviews_count'], 1)
        print(json.dumps(response.data, indent=2))

    def test_future_review_counts_preprocessor_does_not_include_currently_active_reviews(self):
        within_day_review = create_review_for_specific_time(self.user, "some word",
                                                            timezone.now() + timedelta(hours=12))
        within_day_review.needs_review = True
        within_day_review.save()

        self.client.force_login(user=self.user)
        response = self.client.get(reverse("api:user-me"))

        self.assertEqual(response.data["profile"]['reviews_within_day_count'], 0)
        self.assertEqual(response.data["profile"]['reviews_within_hour_count'], 0)
        self.assertEqual(response.data["profile"]['reviews_count'], 2)

    def test_review_count_preprocessor_returns_sane_values_when_user_has_no_vocabulary_unlocked(self):
        self.review.delete()

        self.client.force_login(user=self.user)
        response = self.client.get(reverse("api:user-me"))

        self.assertEqual(response.data["profile"]['reviews_within_day_count'], 0)
        self.assertEqual(response.data["profile"]['reviews_within_hour_count'], 0)
        self.assertEqual(response.data["profile"]['reviews_count'], 0)

    def test_preprocessor_srs_counts_are_correct(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse("api:user-me"))

        self.assertEqual(response.data['profile']['srs_counts']['Apprentice'], 1)
        self.assertEqual(response.data['profile']['srs_counts']['Guru'], 0)
        self.assertEqual(response.data['profile']['srs_counts']['Master'], 0)
        self.assertEqual(response.data['profile']['srs_counts']['Enlightened'], 0)
        self.assertEqual(response.data['profile']['srs_counts']['Burned'], 0)

    def test_updating_profile_triggers_srs_correctly(self):
        self.client.force_login(user=self.user)
        #response = self.client.get(reverse("api:profile-detail", (self.user.profile.id,)))
        response = self.client.get(reverse("api:user-me"))

        self.assertEqual(response.data['profile']['srs_counts']['Apprentice'], 1)
        self.assertEqual(response.data['profile']['srs_counts']['Guru'], 0)
        self.assertEqual(response.data['profile']['srs_counts']['Master'], 0)
        self.assertEqual(response.data['profile']['srs_counts']['Enlightened'], 0)
        self.assertEqual(response.data['profile']['srs_counts']['Burned'], 0)
        user_dict = dict(response.data)
        user_dict['profile']['on_vacation'] = True
        user_dict['profile']['follow_me'] = True
        #self.client.put(reverse("api:profile-detail", (self.user.profile.id,)), user_dict, format='json')
        response = self.client.put(reverse("api:user-me"), user_dict, format='json')
        print("test")
