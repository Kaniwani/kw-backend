from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.tests.utils import (
    setupTestFixture,
)


class TestLesson(APITestCase):
    def setUp(self):
        setupTestFixture(self)

    def test_correct_does_not_increment_upon_lesson_completion(self):
        # Given
        self.client.force_login(self.user)
        self.review.streak = 0
        self.review.save()

        # When
        self.client.post(reverse("api:review-correct", args=(self.review.id,)))

        # Then
        response = self.client.get(
            reverse("api:review-detail", args=(self.review.id,))
        )
        review = response.data
        self.assertEqual(review["correct"], 0)
        self.assertEqual(review["streak"], 1)
