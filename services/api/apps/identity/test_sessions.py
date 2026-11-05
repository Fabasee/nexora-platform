from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.identity.models import IdentityProviderAccount, IdentitySession, NexoraUser, SecurityEvent
from apps.identity.security import record_security_event


class SecurityEventRecordingTests(TestCase):
    def setUp(self):
        self.user = NexoraUser.objects.create_user()
        self.request = type("Request", (), {
            "META": {
                "REMOTE_ADDR": "192.0.2.15",
                "HTTP_USER_AGENT": "Test Agent",
                "HTTP_X_REQUEST_ID": "req-test-1",
            }
        })()

    def test_events_without_dedupe_key_are_always_appended(self):
        first = record_security_event(
            user=self.user, event_type=SecurityEvent.EventType.AUTHENTICATED,
            request=self.request, provider="firebase",
        )
        second = record_security_event(
            user=self.user, event_type=SecurityEvent.EventType.SESSION_REVOKED,
            request=self.request, provider="firebase",
        )
        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(SecurityEvent.objects.count(), 2)

    def test_events_with_same_dedupe_key_are_idempotent(self):
        first = record_security_event(
            user=self.user, event_type=SecurityEvent.EventType.AUTHENTICATED,
            request=self.request, provider="firebase", dedupe_key="stable-key",
        )
        second = record_security_event(
            user=self.user, event_type=SecurityEvent.EventType.AUTHENTICATED,
            request=self.request, provider="firebase", dedupe_key="stable-key",
        )
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(SecurityEvent.objects.count(), 1)


class OfficeSessionGovernanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.operator = NexoraUser.objects.create_user()
        self.target = NexoraUser.objects.create_user()
        self.account = IdentityProviderAccount.objects.create(
            user=self.target, provider="firebase", provider_subject="firebase-target",
        )
        now = timezone.now()
        self.session_one = IdentitySession.objects.create(
            provider_account=self.account, authenticated_at=now - timedelta(hours=2),
            last_seen_at=now - timedelta(minutes=5), source_ip="192.0.2.10",
            user_agent="Android Chrome",
        )
        self.session_two = IdentitySession.objects.create(
            provider_account=self.account, authenticated_at=now - timedelta(hours=1),
            last_seen_at=now, source_ip="192.0.2.11", user_agent="Windows Firefox",
        )

    def _authorized(self, method, path):
        self.client.force_authenticate(user=self.operator)
        with patch("apps.identity.office_access.OfficeAccessPermission.has_permission", return_value=True):
            return getattr(self.client, method)(path)

    def test_inventory_lists_active_sessions_and_device_metadata(self):
        response = self._authorized("get", "/api/v1/office/access/sessions/?active=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["user_agent"], "Windows Firefox")
        self.assertIn("source_ip", response.data["results"][0])

    def test_inventory_rejects_invalid_user_uuid(self):
        response = self._authorized("get", "/api/v1/office/access/sessions/?user_id=not-a-uuid")
        self.assertEqual(response.status_code, 400)

    def test_single_session_revocation_is_audited_with_operator_actor(self):
        response = self._authorized(
            "post", f"/api/v1/office/access/sessions/{self.session_one.pk}/revoke/"
        )
        self.assertEqual(response.status_code, 200)
        self.session_one.refresh_from_db()
        self.assertIsNotNone(self.session_one.revoked_at)
        event = SecurityEvent.objects.get(event_type=SecurityEvent.EventType.SESSION_REVOKED)
        self.assertEqual(event.user_id, self.target.pk)
        self.assertEqual(event.actor_id, self.operator.pk)

    def test_bulk_revocation_releases_all_target_sessions_and_audits_each(self):
        response = self._authorized(
            "post", f"/api/v1/office/access/users/{self.target.pk}/sessions/revoke/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["revoked_count"], 2)
        self.assertFalse(IdentitySession.objects.filter(
            provider_account=self.account, revoked_at__isnull=True,
        ).exists())
        self.assertEqual(SecurityEvent.objects.filter(
            user=self.target, event_type=SecurityEvent.EventType.SESSION_REVOKED,
        ).count(), 2)
