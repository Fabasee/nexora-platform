from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APIClient

from apps.identity.models import NexoraUser, SecurityEvent
from apps.identity.office_access import OFFICE_ROLE_PERMISSIONS, OfficeAccessPermission


class OfficeAccessGovernanceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = NexoraUser.objects.create_user()
        self.staff.is_staff = True
        self.staff.save(update_fields=("is_staff",))
        self.viewer = Group.objects.create(name="Office Portfolio Viewer")
        self.staff.groups.add(self.viewer)
        self.regular = NexoraUser.objects.create_user()

    def _get(self, path, user):
        self.client.force_authenticate(user=user)
        def permission(request, view):
            return (
                request.user.is_authenticated and request.user.is_active and request.user.is_staff
                and getattr(view, "office_permission", "") in __import__(
                    "apps.identity.office_access", fromlist=["get_office_permissions"]
                ).get_office_permissions(request.user)
            )
        with patch("apps.identity.office_access.OfficeAccessPermission.has_permission", side_effect=permission):
            return self.client.get(path)

    def test_portfolio_viewer_can_view_self_profile_but_not_security_events(self):
        profile = self._get("/api/v1/office/access/me/", self.staff)
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.data["roles"], ["Office Portfolio Viewer"])
        denied = self._get("/api/v1/office/access/security-events/", self.staff)
        self.assertEqual(denied.status_code, 403)

    def test_staff_without_office_role_is_denied(self):
        denied = self._get("/api/v1/office/access/me/", self.regular)
        self.assertEqual(denied.status_code, 403)

    def test_security_admin_can_read_security_events(self):
        security_admin = NexoraUser.objects.create_user()
        security_admin.is_staff = True
        security_admin.save(update_fields=("is_staff",))
        role = Group.objects.create(name="Office Security Admin")
        security_admin.groups.add(role)
        SecurityEvent.objects.create(
            user=security_admin,
            event_type=SecurityEvent.EventType.AUTHENTICATED,
            provider="firebase",
            source_ip="192.0.2.10",
        )
        response = self._get("/api/v1/office/access/security-events/", security_admin)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["event_type"], "identity.authenticated")

    def test_permission_requires_verified_email_even_with_valid_role(self):
        request = SimpleNamespace(user=self.staff, nexora_email_verified=False)
        view = SimpleNamespace(office_permission="portfolio.view")
        self.assertFalse(OfficeAccessPermission().has_permission(request, view))
        request.nexora_email_verified = True
        self.assertTrue(OfficeAccessPermission().has_permission(request, view))

    def test_role_matrix_is_explicit_and_least_privilege(self):
        self.assertNotIn("access.manage", OFFICE_ROLE_PERMISSIONS["Office Portfolio Viewer"])
        self.assertIn("access.manage", OFFICE_ROLE_PERMISSIONS["Office Security Admin"])
