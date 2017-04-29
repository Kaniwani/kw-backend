from datetime import timedelta
from unittest import mock

import responses
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden
from django.test import TestCase, Client
from django.utils import timezone

from kw_webapp.tasks import build_API_sync_string_for_user_for_levels
from kw_webapp.tests import sample_api_responses
from kw_webapp.tests.utils import create_user, create_userspecific, create_profile, create_reading
from kw_webapp.tests.utils import create_vocab


class TestViews(TestCase):
    def setUp(self):
        self.user = create_user("user1")
        self.user.set_password("password")
        self.user.save()
        create_profile(self.user, "some_key", 5)
        # create a piece of vocab with one reading.
        self.vocabulary = create_vocab("radioactive bat")
        self.cat_reading = create_reading(self.vocabulary, "kana", "kanji", 5)

        # setup a review with two synonyms
        self.review = create_userspecific(self.vocabulary, self.user)

        self.client = Client()
        self.client.login(username="user1", password="password")

    @responses.activate
    def test_sync_now_endpoint_returns_correct_json(self):
        responses.add(responses.GET,
                      "https://www.wanikani.com/api/user/{}/user-information".format(self.user.profile.api_key),
                      json=sample_api_responses.user_information_response,
                      status=200,
                      content_type="application/json")

        responses.add(responses.GET, build_API_sync_string_for_user_for_levels(self.user, [5, 17]) + ",",
                      json=sample_api_responses.single_vocab_response,
                      status=200,
                      content_type='application/json')

        response = self.client.get(reverse("kw:sync"), data={"full_sync": "true"})

        correct_response = {
            "new_review_count": 0,
            "profile_sync_succeeded": True,
            "new_synonym_count": 0
        }

        self.assertJSONEqual(str(response.content, encoding='utf8'), correct_response)


    def test_removing_synonym_removes_synonym(self):
        dummy_kana = "whatever"
        dummy_characters = "somechar"
        synonym, created = self.review.add_answer_synonym(dummy_kana, dummy_characters)

        self.client.post(reverse("kw:remove_synonym"), data={"synonym_id": synonym.id})

        self.review.refresh_from_db()

        self.assertListEqual(self.review.answer_synonyms_list(), [])


    def test_review_submission_correctly_rounds_time_up_to_next_interval(self):
        original_time = self.review.next_review_date

        #prep work to grab the actual correct time
        self.review.streak += 1
        self.review.save()
        self.review.set_next_review_time()
        self.review.refresh_from_db()
        correct_time = self.review.next_review_date
        self.review.next_review_date = original_time
        self.review.streak -= 1
        self.review.save()

        self.client.post(reverse("kw:record_answer"), data={'user_correct': "true", 'user_specific_id': self.review.id, 'wrong_before': 'false'})

        self.review.refresh_from_db()

        self.assertAlmostEqual(correct_time, self.review.next_review_date, delta=timedelta(seconds=1))

    def test_early_termination_redirects_to_home_when_no_reviews_were_done(self):

        response = self.client.post(reverse("kw:summary"), follow=True)

        self.assertRedirects(response, reverse("kw:home"))

    def test_reviewing_that_does_not_need_to_be_reviewed_fails(self):
        self.review.needs_review = False
        self.review.save()

        response = self.client.post(reverse("kw:record_answer"),data={'user_correct': "true", 'user_specific_id': self.review.id, 'wrong_before': 'false'})
        self.assertTrue(isinstance(response, HttpResponseForbidden))
