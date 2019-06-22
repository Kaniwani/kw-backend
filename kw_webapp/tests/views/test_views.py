from datetime import timedelta
from unittest import mock

import responses
from django.http import HttpResponseForbidden
from django.test import TestCase, Client
from django.utils import timezone
from rest_framework.reverse import reverse

from kw_webapp.tasks import build_API_sync_string_for_user_for_levels
from kw_webapp.tests import sample_api_responses
from kw_webapp.tests.utils import (
    create_user,
    create_review,
    create_profile,
    create_reading,
)
from kw_webapp.tests.utils import create_vocab


class TestViews(TestCase):
    def setUp(self):
        self.user = create_user("user1")
        self.user.set_password("password")
        self.user.save()
        create_profile(self.user, "some_key", 5)
        # create a piece of vocab with one reading.
        self.vocabulary = create_vocab("radioactive bat")
        self.cat_reading = create_reading(self.vocabulary, "ねこ", "猫", 5)

        # setup a review with two synonyms
        self.review = create_review(self.vocabulary, self.user)

        self.client = Client()
        self.client.login(username="user1", password="password")

    def test_removing_synonym_removes_synonym(self):
        dummy_kana = "whatever"
        dummy_characters = "somechar"
        synonym, created = self.review.add_answer_synonym(
            dummy_kana, dummy_characters
        )

        self.client.delete(
            reverse("api:reading-synonym-detail", args=(synonym.id,))
        )

        self.review.refresh_from_db()

        self.assertListEqual(self.review.reading_synonyms_list(), [])

    def test_reviewing_that_does_not_need_to_be_reviewed_fails(self):
        self.review.needs_review = False
        self.review.save()

        response = self.client.post(
            reverse("api:review-correct", args=(self.review.id,)),
            data={"wrong_before": "false"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertIsNotNone(response.data["detail"])

        response = self.client.post(
            reverse("api:review-incorrect", args=(self.review.id,))
        )
        self.assertEqual(response.status_code, 403)
        self.assertIsNotNone(response.data["detail"])

    def test_sending_contact_email_returns_json_response(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("api:contact-list"),
            data={"name": "test", "email": "test@test.com", "body": "test"},
        )
        json = response.content
        self.assertIsNotNone(json)
