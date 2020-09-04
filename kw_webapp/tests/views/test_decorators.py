from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.constants import WkSrsLevel
from kw_webapp.tests.utils import (
    create_lesson,
    create_vocab,
    create_review,
    setupTestFixture, mock_invalid_api_user_info_response_v2, mock_401_for_any_request,
)
import responses


class TestLesson(APITestCase):
    def setUp(self):
        setupTestFixture(self)

    @responses.activate
    def test_checks_wanikani_decorator_on_reset(self):
        self.client.force_login(self.user)
        self.user.profile.api_key = "definitelybrokenAPIkey"
        self.user.profile.save()
        mock_invalid_api_user_info_response_v2()

        response = self.client.post(
            reverse("api:user-reset"), data={"level": 1}
        )
        assert response.status_code == 400

        self.user.profile.refresh_from_db()
        assert not self.user.profile.api_valid

    @responses.activate
    def test_checks_wanikani_decorator_on_unlock(self):
        self.client.force_login(self.user)
        self.user.profile.api_key = "definitelybrokenAPIkey"
        self.user.profile.save()

        mock_401_for_any_request()

        response = self.client.post(
            reverse("api:level-unlock", args=(self.user.profile.level - 1,))
        )
        assert response.status_code == 400

        self.user.profile.refresh_from_db()
        assert not self.user.profile.api_valid
