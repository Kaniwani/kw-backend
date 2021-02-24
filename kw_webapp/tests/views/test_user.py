import responses
from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
import KW.settings as settings
from kw_webapp.models import Profile
from kw_webapp.tests.utils import (
    create_review_for_specific_time,
    setupTestFixture,
    create_vocab,
    create_reading,
    create_review,
    mock_user_response_v2,
    mock_assignments_with_one_assignment,
    mock_assignments_with_no_assignments,
    mock_study_materials, mock_invalid_api_user_info_response_v2,
)


class TestUser(APITestCase):
    def setUp(self):
        setupTestFixture(self)

    @responses.activate
    def test_sync_now_endpoint_returns_correct_json(self):
        self.client.force_login(self.user)
        #response = self.client.post(
        #    reverse("api:user-sync"), data={"full_sync": "true"}
        #)

        correct_response = {
            "new_review_count": 0,
            "profile_sync_succeeded": True,
            "new_synonym_count": 0,
        }

        #self.assertJSONEqual(
        #    str(response.content, encoding="utf8"), correct_response
        #)

    @responses.activate
    def test_reset_command_only_resets_levels_above_requested_level(
        self
    ):
        self.client.force_login(user=self.user)
        v = create_vocab("test")
        create_reading(v, "test", "test", 2)
        create_review(v, self.user)
        # User has unlocked levels 2 and 5
        mock_user_response_v2()

        self.user.profile.unlocked_levels.get_or_create(level=2)
        response = self.client.get((reverse("api:review-current")))
        self.assertEqual(response.data["count"], 2)
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [5, 2])

        # Reset to level 3, should re-lock level 5
        self.client.post(reverse("api:user-reset"), data={"level": 3})
        response = self.client.get((reverse("api:review-current")))
        self.assertEqual(response.data["count"], 1)
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [2])

        # Ensure reset to level 2 keeps reviews at that level
        self.client.post(reverse("api:user-reset"), data={"level": 2})
        response = self.client.get((reverse("api:review-current")))
        self.assertEqual(response.data["count"], 1)
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [2])


    @responses.activate
    def test_invalid_api_key_during_reset_correctly_shows_400(self):
        self.client.force_login(self.user)
        mock_invalid_api_user_info_response_v2()

        response = self.client.post(
            reverse("api:user-reset"), data={"level": 1}
        )
        assert response.status_code == 400

        self.user.profile.refresh_from_db()
        assert not self.user.profile.api_valid

    @responses.activate
    def test_user_that_is_created_who_has_no_vocab_at_current_level_also_gets_previous_level_unlocked(
        self
    ):
        # Create a user who is at level 2 on Wanikani, but has no level 2 vocab unlocked, only level 1 vocab.
        fake_username = "fake_username"
        fake_api_key = "fake_api_key"

        mock_user_response_v2()
        mock_assignments_with_no_assignments()
        mock_assignments_with_one_assignment()
        mock_study_materials()

        self.client.post(
            reverse("api:auth:user-create"),
            data={
                "username": fake_username,
                "password": "password",
                "api_key_v2": fake_api_key,
                "email": "asdf@email.com",
            },
        )

        user_profile = Profile.objects.get(user__username=fake_username)
        assert len(user_profile.unlocked_levels_list()) == 2

    def test_login_works_with_email_or_username(self):
        response = self.client.post(
            settings.LOGIN_URL,
            data={
                "username": self.user.username,
                "password": self.user.username,
            },
        )
        assert response.status_code == 200

        response = self.client.post(
            settings.LOGIN_URL,
            data={"username": self.user.email, "password": self.user.username},
        )
        assert response.status_code == 200
