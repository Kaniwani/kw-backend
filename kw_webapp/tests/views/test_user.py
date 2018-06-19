from datetime import timedelta

import responses
from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.tasks import build_API_sync_string_for_user_for_levels
from kw_webapp.tests import sample_api_responses
from kw_webapp.tests.utils import create_review_for_specific_time, mock_user_info_response_with_higher_level, \
    setupTestFixture, create_vocab, create_reading, create_review, mock_user_info_response


class TestUser(APITestCase):

    def setUp(self):
        setupTestFixture(self)

    @responses.activate
    def test_sync_now_endpoint_returns_correct_json(self):
        self.client.force_login(self.user)
        responses.add(responses.GET,
                      "https://www.wanikani.com/api/user/{}/user-information".format(self.user.profile.api_key),
                      json=sample_api_responses.user_information_response_with_higher_level,
                      status=200,
                      content_type="application/json")

        responses.add(responses.GET, build_API_sync_string_for_user_for_levels(self.user, [5, 17]),
                      json=sample_api_responses.single_vocab_response,
                      status=200,
                      content_type='application/json')


        response = self.client.post(reverse("api:user-sync"), data={"full_sync": "true"})

        correct_response = {
            "new_review_count": 0,
            "profile_sync_succeeded": True,
            "new_synonym_count": 0
        }

        self.assertJSONEqual(str(response.content, encoding='utf8'), correct_response)

    @responses.activate
    def test_adding_a_level_to_reset_command_only_resets_levels_above_or_equal_togiven(self):
        self.client.force_login(user=self.user)
        v = create_vocab("test")
        create_reading(v, "test", "test", 3)
        create_review(v, self.user)
        mock_user_info_response(self.user.profile.api_key)

        self.user.profile.unlocked_levels.get_or_create(level=2)
        response = self.client.get((reverse("api:review-current")))
        self.assertEqual(response.data['count'], 2)
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [5,2])
        self.client.post(reverse("api:user-reset"), data={'level': 3})

        response = self.client.get((reverse("api:review-current")))
        self.assertEqual(response.data['count'], 0)
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [2])

    @responses.activate
    def test_when_user_resets_account_to_a_given_level_their_current_level_is_also_set(self):
        # Given
        mock_user_info_response_with_higher_level(self.user.profile.api_key)
        self.client.force_login(self.user)
        assert(self.user.profile.level == 5)

        # When
        response = self.client.post(reverse("api:user-reset"), data={'level': 1})
        assert("Your account has been reset" in response.data['message'])

        # Then
        self.user.profile.refresh_from_db()
        assert(self.user.profile.level == 17)
