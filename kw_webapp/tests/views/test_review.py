from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.constants import WkSrsLevel, WANIKANI_SRS_LEVELS
from kw_webapp.tests.utils import create_lesson, create_vocab, create_review, setupTestFixture


class TestReview(APITestCase):

    def setUp(self):
        setupTestFixture(self)

    def test_review_counts_endpoints(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("api:review-counts"))
        data = response.data
        self.assertIsNotNone(data['reviews_count'])
        self.assertIsNotNone(data['lessons_count'])

    def test_resetting_a_review_resets_all_data(self):
        self.client.force_login(self.user)

        # Burn a review
        self.review.streak = 9
        self.review.correct = 9
        self.review.burned = True
        self.review.last_studied = timezone.now()
        self.review.next_review_date = None
        self.review.save()

        # Ensure does not need to be reviewed
        resp = self.client.get(reverse("api:review-current"))
        self.assertEqual(resp.data["count"], 0)

        # Reset the review.
        resp = self.client.post(reverse("api:review-reset", args=(self.review.id,)))
        self.assertEqual(resp.status_code, 204)

        # Ensure it now needs to be reviewed.
        resp = self.client.get(reverse("api:review-current"))
        self.assertEqual(resp.data["count"], 1)

    def test_review_counts_endpoint_returns_correct_information(self):
        self.client.force_login(self.user)

        # Our initial review should be ready to review.
        response = self.client.get(reverse("api:review-counts"))
        self.assertEqual(response.data['reviews_count'], 1)
        self.assertEqual(response.data['lessons_count'], 0)

        create_lesson(create_vocab("new_lesson"), self.user)

        # Now we should have 1 lesson and 1 review.
        response = self.client.get(reverse("api:review-counts"))
        self.assertEqual(response.data['reviews_count'], 1)
        self.assertEqual(response.data['lessons_count'], 1)


    def test_nonexistent_user_specific_id_raises_error_in_record_answer(self):
        self.client.force_login(user=self.user)
        non_existent_review_id = 9999

        response = self.client.post(reverse("api:review-correct", args=(non_existent_review_id,)),
                                    data={'wrong_before': 'false'})

        self.assertEqual(response.status_code, 404)

    def test_lesson_route_returns_srs_0_reviews(self):
        self.client.force_login(user=self.user)

        # Create a lesson
        new_review = create_review(create_vocab("sample"), self.user)
        new_review.streak = 0
        new_review.save()

        response = self.client.get(reverse("api:review-lesson"))
        self.assertEqual(response.data["count"], 1)

    def test_user_getting_answer_wrong_cannot_drop_below_1_in_reviews(self):
        self.client.force_login(user=self.user)
        self.review.streak = 1
        self.review.save()

        self.client.post(reverse("api:review-incorrect", args=(self.review.id,)))
        self.review.refresh_from_db()
        self.assertEqual(self.review.streak, 1)

    def test_reviews_endpoint_omits_lessons(self):
        self.client.force_login(user=self.user)

        # Create a lesson
        new_review = create_review(create_vocab("sample"), self.user)
        new_review.streak = 0
        new_review.save()

        response = self.client.get(reverse("api:review-current"))
        self.assertEqual(response.data["count"], 1)

    def test_once_user_answers_lesson_once_it_becomes_review(self):
        self.client.force_login(user=self.user)

        # Create a lesson
        new_review = create_review(create_vocab("sample"), self.user)
        new_review.streak = 0
        new_review.save()

        response = self.client.get(reverse("api:review-lesson"))
        self.assertEqual(response.data["count"], 1)

        self.client.post(reverse("api:review-correct", args=(new_review.id,)))
        self.review.refresh_from_db()

        response = self.client.get(reverse("api:review-lesson"))
        self.assertEqual(response.data["count"], 0)

    def test_review_views_nested_vocabulary_omits_review_field(self):
        self.client.force_login(user=self.user)

        response = self.client.get(reverse("api:review-detail", args=(self.review.id,)))

        self.assertTrue('review' not in response.data['vocabulary'])

    def test_review_requires_login(self):
        response = self.client.get(reverse("api:review-current"))
        self.assertEqual(response.status_code, 401)

    def test_recording_answer_works_on_correct_answer(self):
        self.client.force_login(user=self.user)

        self.client.post(reverse("api:review-correct", args=(self.review.id,)), data={"wrong_before": "false"})
        self.review.refresh_from_db()

        self.assertEqual(self.review.correct, 1)
        self.assertTrue(self.review.streak == 2)
        self.assertFalse(self.review.needs_review)

    def test_wrong_answer_records_failure(self):
        self.client.force_login(user=self.user)

        self.client.post(reverse("api:review-incorrect", args=(self.review.id,)))
        self.review.refresh_from_db()

        self.assertTrue(self.review.incorrect == 1)
        self.assertTrue(self.review.correct == 0)
        self.assertTrue(self.review.streak == 1)
        self.assertTrue(self.review.needs_review)

    def test_review_page_shows_all_items_when_burnt_setting_is_disabled(self):
        self.client.force_login(user=self.user)
        word = create_vocab("phlange")
        self.user.profile.minimum_wk_srs_level_to_review = WkSrsLevel.APPRENTICE.name
        self.user.profile.save()
        another_review = create_review(word, self.user)
        another_review.wanikani_srs_numeric = 5
        another_review.save()

        response = self.client.get(reverse("api:review-current"))

        self.assertContains(response, "radioactive bat")
        self.assertContains(response, "phlange")

    def test_filtering_on_wk_srs_levels_works(self):
        self.client.force_login(user=self.user)
        word = create_vocab("phlange")
        self.user.profile.minimum_wk_srs_level_to_review = WkSrsLevel.BURNED.name
        self.user.profile.save()
        another_review = create_review(word, self.user)
        another_review.wanikani_srs_numeric = WANIKANI_SRS_LEVELS[WkSrsLevel.BURNED.name][0]
        another_review.save()

        response = self.client.get(reverse("api:review-current"))

        self.assertNotContains(response, "radioactive bat")
        self.assertContains(response, "phlange")

    def test_review_correct_submissions_return_full_modified_review_object(self):
        self.client.force_login(self.user)
        previous_streak = self.review.streak
        previous_correct = self.review.correct

        response = self.client.post(reverse("api:review-correct", args=(self.review.id,)))
        self.assertEqual(response.data['id'], self.review.id)
        self.assertEqual(response.data['streak'], previous_streak + 1)
        self.assertEqual(response.data['correct'], previous_correct + 1)

    def test_setting_reviews_to_order_by_level_works(self):
        pass

    def test_review_filtering_by_maximum_wk_srs_level(self):
        self.client.force_login(self.user)

        self.user.profile.maximum_wk_srs_level_to_review = WkSrsLevel.APPRENTICE.name
        self.user.profile.save()

        self.review.wanikani_srs_numeric = 5
        self.review.wanikani_srs = WkSrsLevel.GURU.name
        self.review.needs_review = True
        self.review.save()

        # Prepare an apprentice review.
        apprentice_review = create_review(create_vocab("new_vocab"), self.user)
        apprentice_review.wanikani_srs_numeric = 1
        apprentice_review.needs_review = True
        apprentice_review.save()

        response = self.client.get(reverse("api:review-current"))
        data = response.data
        self.assertEqual(data["count"], 1)
        # Ensure that any reviews tha tare apprentice on WK are not shown.


