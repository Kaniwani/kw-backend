from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.tests.utils import setupTestFixture


class TestReadingSynonym(APITestCase):
    def setUp(self):
        setupTestFixture(self)

    def test_adding_synonym_adds_synonym(self):
        self.client.force_login(user=self.user)
        synonym_kana = "いぬ"
        synonym_kanji = "犬"
        s1 = reverse("api:reading-synonym-list")
        response = self.client.get(s1)
        self.assertEqual(response.data["count"], 0)

        response = self.client.post(
            s1,
            data={
                "review": self.review.id,
                "kana": synonym_kana,
                "character": synonym_kanji,
            },
        )

        self.review.refresh_from_db()
        found_synonym = self.review.reading_synonyms.first()

        self.assertTrue(synonym_kana in self.review.reading_synonyms_list())
        self.assertEqual(found_synonym.kana, synonym_kana)
        self.assertEqual(found_synonym.character, synonym_kanji)
