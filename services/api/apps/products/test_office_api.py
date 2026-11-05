from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.identity.models import NexoraUser
from .models import ProductPortfolioEntry


class OfficePortfolioApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff_user = NexoraUser.objects.create_user()
        self.staff_user.is_staff = True
        self.staff_user.save(update_fields=("is_staff",))
        self.regular_user = NexoraUser.objects.create_user()
        self.application = ProductPortfolioEntry.objects.create(
            key="office-test-app",
            name="Office Test App",
            entry_type=ProductPortfolioEntry.EntryType.APPLICATION,
            category="Test",
            lifecycle_status=ProductPortfolioEntry.LifecycleStatus.PLANNED,
            decision_status=ProductPortfolioEntry.DecisionStatus.CONFIRMED,
            priority=ProductPortfolioEntry.Priority.CORE,
            delivery_model=ProductPortfolioEntry.DeliveryModel.STANDALONE,
        )
        ProductPortfolioEntry.objects.create(
            key="office-test-module",
            name="Office Test Module",
            entry_type=ProductPortfolioEntry.EntryType.MODULE,
            category="Test",
            parent=self.application,
            lifecycle_status=ProductPortfolioEntry.LifecycleStatus.RESEARCH,
            decision_status=ProductPortfolioEntry.DecisionStatus.CANDIDATE,
            priority=ProductPortfolioEntry.Priority.FUTURE,
            delivery_model=ProductPortfolioEntry.DeliveryModel.MODULE,
        )

    def _staff_get(self, path, params=None):
        self.client.force_authenticate(user=self.staff_user)
        with patch(
            "apps.identity.permissions.VerifiedEmailRequired.has_permission",
            return_value=True,
        ):
            return self.client.get(path, data=params)

    def test_anonymous_user_cannot_access_office_portfolio(self):
        response = self.client.get("/api/v1/office/portfolio/")
        self.assertEqual(response.status_code, 401)

    def test_regular_authenticated_user_cannot_access_office_portfolio(self):
        self.client.force_authenticate(user=self.regular_user)
        with patch(
            "apps.identity.permissions.VerifiedEmailRequired.has_permission",
            return_value=True,
        ):
            response = self.client.get("/api/v1/office/portfolio/")
        self.assertEqual(response.status_code, 403)

    def test_staff_can_list_and_filter_portfolio(self):
        response = self._staff_get(
            "/api/v1/office/portfolio/",
            {"entry_type": "module", "decision_status": "candidate"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["key"], "office-test-module")

    def test_invalid_filter_is_rejected(self):
        response = self._staff_get(
            "/api/v1/office/portfolio/",
            {"lifecycle_status": "not-a-status"},
        )
        self.assertEqual(response.status_code, 400)

    def test_staff_can_read_hierarchy_detail_and_summary(self):
        detail = self._staff_get("/api/v1/office/portfolio/office-test-app/")
        summary = self._staff_get("/api/v1/office/summary/")

        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["module_count"], 1)
        self.assertEqual(detail.data["modules"][0]["key"], "office-test-module")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.data["total_entries"], 2)
        self.assertEqual(summary.data["applications"], 1)
        self.assertEqual(summary.data["modules"], 1)

    def test_detail_does_not_disclose_unknown_entries(self):
        response = self._staff_get("/api/v1/office/portfolio/not-found/")
        self.assertEqual(response.status_code, 404)
