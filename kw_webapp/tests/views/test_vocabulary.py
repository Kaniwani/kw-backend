from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.constants import WkSrsLevel
from kw_webapp.tests.utils import (
    create_review,
    create_vocab,
    create_reading,
    setupTestFixture,
)


class TestVocabulary(APITestCase):
    def setUp(self):
        setupTestFixture(self)

    def test_vocabulary_view_returns_related_review_id_if_present(self):
        self.client.force_login(user=self.user)

        response = self.client.get(
            reverse("api:vocabulary-detail", args=(self.review.vocabulary.id,))
        )

        self.assertEqual(response.data["review"], self.review.id)

    def test_fetching_vocabulary_shows_is_reviable_field_on_associated_vocabulary(self):
        self.client.force_login(self.user)

        self.review.wanikani_srs_numeric = 1
        self.review.save()

        wk_burned_review = create_review(create_vocab("test"), self.user)
        wk_burned_review.wanikani_srs_numeric = 9
        wk_burned_review.save()

        self.user.profile.minimum_wk_srs_level_to_review = WkSrsLevel.BURNED.name
        self.user.profile.save()
        response = self.client.get(reverse("api:vocabulary-list"))
        data = response.data

        assert data["results"][0]["is_reviewable"] is False
        assert data["results"][1]["is_reviewable"] is True

    def test_meaning_contains_checks_for_word_boundaries(self):
        self.client.force_login(self.user)
        create_vocab("frog")
        create_vocab("puppy")
        create_vocab("up, upwards")
        create_vocab("not down, up")

        response = self.client.get(
            reverse("api:vocabulary-list") + "?meaning_contains=up"
        )
        data = response.data
        assert len(data["results"]) == 2

    def test_searching_based_on_reading_returns_distinct_responses(self):
        reading_to_search = "eyylmao"
        v = create_vocab("vocabulary with 2 readings.")
        create_reading(v, reading_to_search, "character_1", 5)
        create_reading(v, reading_to_search, "character_2", 5)

        review = create_review(v, self.user)
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("api:vocabulary-list")
            + "?reading_contains={}".format(reading_to_search)
        )
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data["results"]), 1)

    def test_sentence_furigana_appears_in_vocabulary_response(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("api:vocabulary-detail", args=(self.vocabulary.id,))
        )
        data = response.data
        self.assertTrue(data["readings"][0]["furigana_sentence_ja"] is not None)
