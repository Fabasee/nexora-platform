from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from unittest.mock import patch

from apps.identity.models import IdentityProviderAccount, IdentitySession, NexoraUser, SecurityEvent
from apps.identity.office_access import get_office_permissions


class OfficeSessionGovernanceTests(TestCase):
    def setUp(self):
        self.operator = NexoraUser.objects.create_user()
        self.operator.is_staff = True
        self.operator.save(update_fields=("is_staff",))
        self.operator.groups.add(Group.objects.create(name="Office Security Admin"))
        self.target = NexoraUser.objects.create_user()
        self.provider = IdentityProviderAccount.objects.create(
            user=self.target, provider="firebase", provider_subject="office-session-target"
        )
        self.session = IdentitySession.objects.create(
            provider_account=self.provider, authenticated_at=timezone.now(),
            last_seen_at=timezone.now(), source_ip="192.0.2.44", user_agent="Test Browser",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.operator)

    def _enable_permission(self):
        patcher = patch(
            "apps.identity.office_access.OfficeAccessPermission.has_permission",
            side_effect=lambda request, view: request.user.is_authenticated and request.user.is_staff
            and getattr(view, "office_permission", "") in get_office_permissions(request.user),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_security_admin_lists_sessions_with_device_context(self):
        self._enable_permission()
        response = self.client.get("/api/v1/office/access/sessions/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["user_id"], str(self.target.pk))
        self.assertEqual(response.data["results"][0]["source_ip"], "192.0.2.44")

    def test_security_admin_can_revoke_session_and_actor_is_recorded(self):
        self._enable_permission()
        response = self.client.post(f"/api/v1/office/access/sessions/{self.session.pk}/revoke/")
        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertIsNotNone(self.session.revoked_at)
        event = SecurityEvent.objects.get(user=self.target, event_type=SecurityEvent.EventType.SESSION_REVOKED)
        self.assertEqual(event.actor_id, self.operator.pk)

    def test_security_admin_can_revoke_all_target_sessions(self):
        self._enable_permission()
        second = IdentitySession.objects.create(
            provider_account=self.provider, authenticated_at=timezone.now(),
            last_seen_at=timezone.now(), user_agent="Second browser",
        )
        response = self.client.post(f"/api/v1/office/access/users/{self.target.pk}/sessions/revoke/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["revoked_count"], 2)
        second.refresh_from_db()
        self.assertIsNotNone(second.revoked_at)

    def test_session_list_rejects_malformed_user_uuid(self):
        self._enable_permission()
        response = self.client.get("/api/v1/office/access/sessions/?user_id=not-a-uuid")
        self.assertEqual(response.status_code, 400)
