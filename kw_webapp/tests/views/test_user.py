from datetime import timedelta

import responses
from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.models import Profile
from kw_webapp.tasks import build_API_sync_string_for_user_for_levels
from kw_webapp.tests import sample_api_responses
from kw_webapp.tests.utils import (
    create_review_for_specific_time,
    mock_user_info_response_with_higher_level,
    setupTestFixture,
    create_vocab,
    create_reading,
    create_review,
    mock_user_info_response,
    mock_user_info_response_at_level_1, mock_empty_vocabulary_response)


class TestUser(APITestCase):
    def setUp(self):
        setupTestFixture(self)

    @responses.activate
    def test_sync_now_endpoint_returns_correct_json(self):
        self.client.force_login(self.user)
        responses.add(
            responses.GET,
            "https://www.wanikani.com/api/user/{}/user-information".format(
                self.user.profile.api_key
            ),
            json=sample_api_responses.user_information_response_with_higher_level,
            status=200,
            content_type="application/json",
        )

        responses.add(
            responses.GET,
            build_API_sync_string_for_user_for_levels(self.user, [5, 17]),
            json=sample_api_responses.single_vocab_response,
            status=200,
            content_type="application/json",
        )

        response = self.client.post(
            reverse("api:user-sync"), data={"full_sync": "true"}
        )

        correct_response = {
            "new_review_count": 0,
            "profile_sync_succeeded": True,
            "new_synonym_count": 0,
        }

        self.assertJSONEqual(str(response.content, encoding="utf8"), correct_response)

    @responses.activate
    def test_adding_a_level_to_reset_command_only_resets_levels_above_or_equal_togiven(
        self
    ):
        self.client.force_login(user=self.user)
        v = create_vocab("test")
        create_reading(v, "test", "test", 3)
        create_review(v, self.user)
        mock_user_info_response(self.user.profile.api_key)

        self.user.profile.unlocked_levels.get_or_create(level=2)
        response = self.client.get((reverse("api:review-current")))
        self.assertEqual(response.data["count"], 2)
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [5, 2])
        self.client.post(reverse("api:user-reset"), data={"level": 3})

        response = self.client.get((reverse("api:review-current")))
        self.assertEqual(response.data["count"], 0)
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [2])

    @responses.activate
    def test_when_user_resets_account_to_a_given_level_their_current_level_is_also_set(
        self
    ):
        # Given
        mock_user_info_response_with_higher_level(self.user.profile.api_key)
        self.client.force_login(self.user)
        assert self.user.profile.level == 5

        # When
        response = self.client.post(reverse("api:user-reset"), data={"level": 1})
        assert "Your account has been reset" in response.data["message"]

        # Then
        self.user.profile.refresh_from_db()
        assert self.user.profile.level == 17

    def test_invalid_api_key_during_reset_correctly_shows_400(self):
        self.client.force_login(self.user)
        self.user.profile.api_key = "definitelybrokenAPIkey"
        self.user.profile.save()

        response = self.client.post(reverse("api:user-reset"), data={"level": 1})
        assert response.status_code == 400

        self.user.profile.refresh_from_db()
        assert not self.user.profile.api_valid

    def test_user_that_is_created_who_has_no_vocab_at_current_level_also_gets_previous_level_unlocked(self):
        pass

    @responses.activate
    def test_user_at_level_one_with_no_vocab_does_not_attempt_to_unlock_previous_level(self):
        # Create a user who is at level 1 on Wanikani
        fake_username = "fake_username"
        fake_api_key = "fake_api_key"
        mock_user_info_response_at_level_1(fake_api_key)
        mock_empty_vocabulary_response(fake_api_key, 1) # Mock an empty response for level 1
        self.client.post(
            reverse("api:auth:user-create"),
            data={
                "username": fake_username,
                "password": "password",
                "api_key": fake_api_key,
                "email": "asdf@email.com",
            },
        )

        user_profile = Profile.objects.get(user__username=fake_username)
        assert len(user_profile.unlocked_levels_list()) == 1







