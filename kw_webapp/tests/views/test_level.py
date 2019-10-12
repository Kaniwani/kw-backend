import re
from unittest import mock

import responses
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.models import Level
from kw_webapp.tests import sample_api_responses
from kw_webapp.tests.utils import setupTestFixture
from kw_webapp.utils import one_time_orphaned_level_clear


class TestLevel(APITestCase):
    def setUp(self):
        self._vocab_api_regex = re.compile(
            r"https://www\.wanikani\.com/api/user/.*"
        )
        setupTestFixture(self)

    def test_locking_current_level_disables_following_setting(self):
        self.client.force_login(user=self.user)
        self.user.profile.follow_me = True
        self.user.profile.level = 5
        self.user.save()

        self.client.post(
            reverse("api:level-lock", args=(self.user.profile.level,))
        )
        response = self.client.get(reverse("api:user-me"))
        self.assertFalse(response.data["profile"]["follow_me"])

    def test_locking_a_level_locks_successfully(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("api:level-lock", args=(self.user.profile.level,))
        )

        self.assertEqual(response.data["locked"], 1)

    def test_user_unlocking_too_high_level_fails(self):
        self.client.force_login(user=self.user)
        self.user.profile.level = 5
        self.user.save()
        level_too_high = 20

        response = self.client.post(
            reverse("api:level-unlock", args=(level_too_high,))
        )
        self.assertEqual(response.status_code, 403)

    @responses.activate
    def test_unlocking_a_level_returns_correct_values(self):
        self.client.force_login(user=self.user)
        self.user.profile.api_valid = True
        self.user.profile.save()
        resp_body = sample_api_responses.single_vocab_response
        responses.add(
            responses.GET,
            self._vocab_api_regex,
            json=resp_body,
            status=200,
            content_type="application/json",
        )
        s1 = reverse("api:level-unlock", args=(5,))

        response = self.client.post(s1)
        self.assertEqual(response.data["total_unlocked"], 1)
        self.assertEqual(response.data["unlocked_now"], 0)
        self.assertEqual(response.data["locked"], 0)

    def test_locking_a_level_successfully_clears_the_level_object(self):
        self.client.force_login(user=self.user)
        level = Level.objects.get(profile=self.user.profile, level=5)
        self.assertTrue(level is not None)

        self.client.post(
            reverse("api:level-lock", args=(self.user.profile.level,))
        )

        levels = Level.objects.filter(profile=self.user.profile, level=5)
        self.assertEqual(levels.count(), 0)

    def test_one_time_orphan_clear_deletes_orphaned_levels(self):
        self.user.profile.unlocked_levels.get_or_create(level=5)[0]
        l6 = self.user.profile.unlocked_levels.get_or_create(level=6)[0]
        l7 = self.user.profile.unlocked_levels.get_or_create(level=7)[0]
        self.user.profile.unlocked_levels.get_or_create(level=8)[0]
        self.user.profile.unlocked_levels.get_or_create(level=9)[0]

        level_count = Level.objects.filter(profile=self.user.profile).count()
        self.assertEqual(level_count, 5)

        self.user.profile.unlocked_levels.remove(l6)
        self.user.profile.unlocked_levels.remove(l7)

        # Oh no two orphaned levels.
        level_count = Level.objects.filter(profile=None).count()
        self.assertEqual(level_count, 2)

        one_time_orphaned_level_clear()

        # Our user has the correct amount of levels associated..
        level_count = Level.objects.filter(profile=self.user.profile).count()
        self.assertEqual(len(self.user.profile.unlocked_levels_list()), 3)

        # No more orphaned levels!
        level_count = Level.objects.filter(profile=None).count()
        self.assertEqual(level_count, 0)
