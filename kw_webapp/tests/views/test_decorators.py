from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.tests.utils import (
    setupTestFixture,
)


class TestLesson(APITestCase):
    def setUp(self):
        setupTestFixture(self)

    def test_checks_wanikani_decorator_on_reset(self):
        self.client.force_login(self.user)
        self.user.profile.api_key = "definitelybrokenAPIkey"
        self.user.profile.save()

        response = self.client.post(
            reverse("api:user-reset"), data={"level": 1}
        )
        assert response.status_code == 400

        self.user.profile.refresh_from_db()
        assert not self.user.profile.api_valid

    def test_checks_wanikani_decorator_on_lock(self):
        self.client.force_login(self.user)
        self.user.profile.api_key = "definitelybrokenAPIkey"
        self.user.profile.save()

        response = self.client.post(
            reverse("api:level-unlock", args=(self.user.profile.level - 1,))
        )
        assert response.status_code == 400

        self.user.profile.refresh_from_db()
        assert not self.user.profile.api_valid
