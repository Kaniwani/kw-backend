import json
import pprint
from datetime import timedelta
from time import sleep
from unittest import mock

from django.utils import timezone
from rest_framework.renderers import JSONRenderer
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from kw_webapp.constants import WkSrsLevel, WANIKANI_SRS_LEVELS
from kw_webapp.models import Level, Report, Announcement
from kw_webapp.tests.utils import create_user, create_profile, create_vocab, create_reading, create_userspecific, \
    create_review_for_specific_time
from kw_webapp.utils import one_time_orphaned_level_clear


class TestMeaningSynonymApi(APITestCase):
    def setUp(self):
        self.user = create_user("Tadgh")
        create_profile(self.user, "any_key", 5)
        self.vocabulary = create_vocab("radioactive bat")
        self.reading = create_reading(self.vocabulary, "ねこ", "猫", 5)
        self.review = create_userspecific(self.vocabulary, self.user)

    def test_user_can_CRUD_all_their_own_synonyms(self):
        self.client.force_login(self.user)

        # Create
        synonym = {
            'review': self.review.id,
            'text': "My fancy synonym"
        }
        response = self.client.post(reverse("api:meaning-synonym-list"), data=synonym)
        self.assertEqual(response.status_code, 201)

        # Read
        self.assertEqual(self.review.synonyms_string(), "My fancy synonym")
        response = self.client.get(reverse("api:meaning-synonym-list"))
        self.assertEqual(response.status_code, 200)
        data = response.data
        synonym = data['results'][0]
        self.assertEqual(len(data['results']), 1)

        # Update
        synonym['text'] = "A different fancy synonym"
        response = self.client.put(reverse("api:meaning-synonym-detail", args=(synonym["id"],)), data=synonym)

        self.assertEqual(response.status_code, 200)
        # Double check update worked...
        self.review.refresh_from_db()
        self.assertEqual(self.review.synonyms_string(), "A different fancy synonym")
        self.assertEqual(len(self.review.synonyms_list()), 1)

        # Delete
        self.client.delete(reverse("api:meaning-synonym-detail", args=(synonym["id"],)))
        self.review.refresh_from_db()
        self.assertEqual(len(self.review.synonyms_list()), 0)




