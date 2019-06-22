from unittest import mock

from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from kw_webapp.models import Level, Report
from kw_webapp.tests.utils import (
    create_user,
    create_profile,
    create_vocab,
    create_reading,
    setupTestFixture,
)


class TestReport(APITestCase):
    def setUp(self):
        setupTestFixture(self)

    def test_reporting_vocab_creates_report(self):
        self.client.force_login(user=self.user)

        self.client.post(
            reverse("api:report-list"),
            data={
                "reading": self.reading.id,
                "reason": "This makes no sense!!!",
            },
        )

        reports = Report.objects.all()

        self.assertEqual(reports.count(), 1)
        report = reports[0]
        self.client.delete(reverse("api:report-detail", args=(report.id,)))
        self.assertEqual(report.reading, self.reading)
        self.assertEqual(report.created_by, self.user)
        self.assertLessEqual(report.created_at, timezone.now())

    def test_report_counts_endpoint(self):
        # Report a vocab.
        self.client.force_login(user=self.user)
        # This should only ever create ONE report, as we continually update the same one. We do not allow users to
        # multi-report a single vocab.
        self.client.post(
            reverse("api:report-list"),
            data={
                "reading": self.reading.id,
                "reason": "This still makes no sense!!!",
            },
        )
        self.client.post(
            reverse("api:report-list"),
            data={"reading": self.reading.id, "reason": "ahhh!!!"},
        )
        self.client.post(
            reverse("api:report-list"),
            data={"reading": self.reading.id, "reason": "Help!"},
        )
        self.client.post(
            reverse("api:report-list"),
            data={"reading": self.reading.id, "reason": "asdf!!!"},
        )
        self.client.post(
            reverse("api:report-list"),
            data={"reading": self.reading.id, "reason": "fdsa!!!"},
        )
        self.client.post(
            reverse("api:report-list"),
            data={"reading": self.reading.id, "reason": "Final report!!!!"},
        )

        # Have another user report it
        user = create_user("test2")
        create_profile(user, "test", 5)
        self.client.force_login(user=user)
        self.client.post(
            reverse("api:report-list"),
            data={
                "reading": self.reading.id,
                "reason": "This still makes no sense!!!",
            },
        )

        # Report another vocab, but only once
        new_vocab = create_vocab("some other vocab")
        reading = create_reading(new_vocab, "reading", "reading_char", 1)

        self.client.post(
            reverse("api:report-list"),
            data={
                "reading": reading.id,
                "reason": "This still makes no sense!!!",
            },
        )

        # Login with admin
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("api:report-counts"))

        assert resp.data[0]["report_count"] > resp.data[1]["report_count"]

        assert resp.data[0]["report_count"] == 2
        assert resp.data[0]["reading"] == self.reading.id

        assert resp.data[1]["report_count"] == 1
        assert resp.data[1]["reading"] == reading.id

        resp = self.client.get(reverse("api:report-list"))
        assert resp.data["count"] == 3
