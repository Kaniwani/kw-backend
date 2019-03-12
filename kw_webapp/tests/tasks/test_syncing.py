import responses
from rest_framework.test import APITestCase

from api.sync.SyncerFactory import Syncer
from kw_webapp.tests.utils import (
    mock_vocab_list_response_with_single_vocabulary_with_four_synonyms,
    setupTestFixture,
)


class TestSyncing(APITestCase):
    def setUp(self):
        setupTestFixture(self)


    @responses.activate
    def test_sync_with_modified_synonyms_replaces_old_synonyms(self):
        self.client.force_login(self.user)
        self.review.meaning_synonyms.get_or_create(text="This will disappear")
        self.review.meaning_synonyms.get_or_create(text="This will also disappear")
        self.assertEqual(len(self.review.meaning_synonyms.all()), 2)

        mock_vocab_list_response_with_single_vocabulary_with_four_synonyms(self.user)

        Syncer.factory(self.user.profile).sync_recent_unlocked_vocab()

        self.review.refresh_from_db()
        self.assertEqual(len(self.review.meaning_synonyms.all()), 4)
