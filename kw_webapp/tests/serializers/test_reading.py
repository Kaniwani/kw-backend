from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.models import MeaningSynonym, AnswerSynonym
from kw_webapp.tests.utils import setupTestFixture


class TestReading(APITestCase):
    def setUp(self):
        setupTestFixture(self)

    def test_review_serializer_shows_both_reading_and_reading_synonyms(self):
        self.client.force_login(self.user)
        meaning_synonym = "Wow a meaning synonym!"
        reading_synonym_kana = "kana"
        reading_synonym_character = "character"

        MeaningSynonym.objects.create(review=self.review, text=meaning_synonym)
        AnswerSynonym.objects.create(
            review=self.review,
            kana=reading_synonym_kana,
            character=reading_synonym_character,
        )

        self.review.refresh_from_db()

        assert len(self.review.meaning_synonyms.all()) > 0
        assert len(self.review.reading_synonyms.all()) > 0
        response = self.client.get(
            reverse("api:review-detail", args=(self.review.id,))
        )
        data = response.data
        assert data["meaning_synonyms"][0]["text"] == meaning_synonym
        assert data["reading_synonyms"][0]["kana"] == reading_synonym_kana
        assert (
            data["reading_synonyms"][0]["character"]
            == reading_synonym_character
        )

        response = self.client.get(reverse("api:review-current"))
        data = response.data
        assert (
            data["results"][0]["meaning_synonyms"][0]["text"]
            == meaning_synonym
        )
        assert (
            data["results"][0]["reading_synonyms"][0]["character"]
            == reading_synonym_character
        )
        assert (
            data["results"][0]["reading_synonyms"][0]["kana"]
            == reading_synonym_kana
        )

        response = self.client.get(reverse("api:review-current"))
        data = response.data
        assert (
            data["results"][0]["meaning_synonyms"][0]["text"]
            == meaning_synonym
        )
        assert (
            data["results"][0]["reading_synonyms"][0]["character"]
            == reading_synonym_character
        )
        assert (
            data["results"][0]["reading_synonyms"][0]["kana"]
            == reading_synonym_kana
        )
        # TODO rework this test to only actually use the serializer.
