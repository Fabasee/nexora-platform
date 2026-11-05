from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.identity.authentication import FirebaseIdentityAuthentication
from apps.identity.models import IdentitySession, SecurityEvent


class AuthenticationContextSignalTests(TestCase):
    @patch("apps.identity.authentication.firebase_auth.verify_id_token")
    @patch("apps.identity.authentication.FirebaseAdminAppFactory.get_app")
    def test_changed_ip_records_informational_event_without_blocking_login(self, get_app, verify_token):
        get_app.return_value = object()
        verify_token.return_value = {
            "uid": "context-change-subject",
            "auth_time": 1_798_000_000,
            "email_verified": True,
        }
        authenticator = FirebaseIdentityAuthentication()
        first = APIRequestFactory().get(
            "/private/", REMOTE_ADDR="192.0.2.10",
            HTTP_USER_AGENT="Nexora Android/1.0",
            HTTP_AUTHORIZATION="Bearer valid-token",
        )
        user, _ = authenticator.authenticate(first)

        verify_token.return_value["auth_time"] = 1_798_000_100
        second = APIRequestFactory().get(
            "/private/", REMOTE_ADDR="198.51.100.20",
            HTTP_USER_AGENT="Nexora Android/1.0",
            HTTP_AUTHORIZATION="Bearer valid-token",
        )
        second_user, _ = authenticator.authenticate(second)

        self.assertEqual(user.pk, second_user.pk)
        self.assertEqual(IdentitySession.objects.filter(provider_account__user=user).count(), 2)
        event = SecurityEvent.objects.get(
            user=user, event_type=SecurityEvent.EventType.AUTH_CONTEXT_CHANGED,
        )
        self.assertEqual(event.source_ip, "198.51.100.20")

    @patch("apps.identity.authentication.firebase_auth.verify_id_token")
    @patch("apps.identity.authentication.FirebaseAdminAppFactory.get_app")
    def test_user_agent_change_is_recorded_but_same_context_is_not(self, get_app, verify_token):
        get_app.return_value = object()
        verify_token.return_value = {
            "uid": "context-agent-subject",
            "auth_time": 1_798_000_000,
            "email_verified": False,
        }
        authenticator = FirebaseIdentityAuthentication()

        def request():
            return APIRequestFactory().get(
                "/private/", REMOTE_ADDR="192.0.2.30",
                HTTP_USER_AGENT="Nexora Android/1.0",
                HTTP_AUTHORIZATION="Bearer valid-token",
            )

        user, _ = authenticator.authenticate(request())
        verify_token.return_value["auth_time"] = 1_798_000_100
        authenticator.authenticate(request())
        self.assertFalse(SecurityEvent.objects.filter(
            user=user, event_type=SecurityEvent.EventType.AUTH_CONTEXT_CHANGED,
        ).exists())

        verify_token.return_value["auth_time"] = 1_798_000_200
        changed = APIRequestFactory().get(
            "/private/", REMOTE_ADDR="192.0.2.30",
            HTTP_USER_AGENT="Nexora iOS/1.0",
            HTTP_AUTHORIZATION="Bearer valid-token",
        )
        authenticator.authenticate(changed)
        self.assertEqual(SecurityEvent.objects.filter(
            user=user, event_type=SecurityEvent.EventType.AUTH_CONTEXT_CHANGED,
        ).count(), 1)
