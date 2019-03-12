from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.constants import WkSrsLevel
from kw_webapp.tasks import build_API_sync_string_for_api_key_for_levels
from kw_webapp.tests.utils import create_lesson, create_vocab, create_review, setupTestFixture, \
    mock_invalid_api_user_info_response
import responses

class TestLesson(APITestCase):

    def setUp(self):
        setupTestFixture(self)

    @responses.activate
    def test_checks_wanikani_decorator_on_reset(self):
        self.client.force_login(self.user)
        self.user.profile.api_key = "definitelybrokenAPIkey"
        self.user.profile.save()
        mock_invalid_api_user_info_response(self.user.profile.api_key)

        response = self.client.post(reverse("api:user-reset"), data={"level": 1})
        assert response.status_code == 400

        self.user.profile.refresh_from_db()
        assert not self.user.profile.api_valid

    @responses.activate
    def test_checks_wanikani_decorator_on_lock(self):
        self.client.force_login(self.user)
        self.user.profile.api_key = "definitelybrokenAPIkey"
        self.user.profile.save()

        responses.add(
            responses.GET,
            build_API_sync_string_for_api_key_for_levels(self.user.profile.api_key, 4),
            json={"Nothing": "Nothing"},
            status=401,
            content_type="application/json",
        )
        response = self.client.post(reverse("api:level-unlock", args=(self.user.profile.level - 1,)))
        assert response.status_code == 400

        self.user.profile.refresh_from_db()
        assert not self.user.profile.api_valid
