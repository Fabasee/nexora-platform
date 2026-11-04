from unittest.mock import patch

from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory, APIClient

from apps.identity.authentication import FirebaseIdentityAuthentication
from apps.identity.models import IdentitySession, SecurityEvent
from apps.identity.services import IdentityService, VerifiedIdentity
from apps.identity.permissions import VerifiedMFARequired


class FirebaseMFAClaimTests(TestCase):
    @patch("apps.identity.authentication.firebase_auth.verify_id_token")
    @patch("apps.identity.authentication.FirebaseAdminAppFactory.get_app")
    def test_verified_totp_claim_marks_session_and_records_event(self, get_app, verify_token):
        get_app.return_value = object()
        verify_token.return_value = {
            "uid": "mfa-totp-subject",
            "auth_time": 1_798_000_000,
            "email_verified": True,
            "firebase": {
                "sign_in_provider": "password",
                "sign_in_second_factor": "totp",
                "second_factor_identifier": "factor-123",
            },
        }
        request = APIRequestFactory().get(
            "/private/", HTTP_AUTHORIZATION="Bearer valid-token",
        )
        user, _ = FirebaseIdentityAuthentication().authenticate(request)
        session = IdentitySession.objects.get(provider_account__user=user)

        self.assertTrue(session.mfa_verified)
        self.assertEqual(session.second_factor_type, "totp")
        self.assertTrue(request.nexora_mfa_verified)
        self.assertEqual(SecurityEvent.objects.filter(
            user=user, event_type=SecurityEvent.EventType.MFA_AUTHENTICATED,
        ).count(), 1)

        FirebaseIdentityAuthentication().authenticate(request)
        self.assertEqual(SecurityEvent.objects.filter(
            user=user, event_type=SecurityEvent.EventType.MFA_AUTHENTICATED,
        ).count(), 1)

    @patch("apps.identity.authentication.firebase_auth.verify_id_token")
    @patch("apps.identity.authentication.FirebaseAdminAppFactory.get_app")
    def test_client_supplied_mfa_flags_are_ignored(self, get_app, verify_token):
        get_app.return_value = object()
        verify_token.return_value = {
            "uid": "mfa-untrusted-subject",
            "auth_time": 1_798_000_001,
            "email_verified": True,
            "mfa_verified": True,
            "second_factor_type": "totp",
        }
        request = APIRequestFactory().get(
            "/private/", HTTP_AUTHORIZATION="Bearer valid-token",
        )
        FirebaseIdentityAuthentication().authenticate(request)
        session = IdentitySession.objects.get()
        self.assertFalse(session.mfa_verified)
        self.assertFalse(request.nexora_mfa_verified)

    @patch("apps.identity.authentication.firebase_auth.verify_id_token")
    @patch("apps.identity.authentication.FirebaseAdminAppFactory.get_app")
    def test_phone_second_factor_is_recognized(self, get_app, verify_token):
        get_app.return_value = object()
        verify_token.return_value = {
            "uid": "mfa-phone-subject",
            "auth_time": 1_798_000_002,
            "firebase": {"sign_in_second_factor": "phone"},
        }
        request = APIRequestFactory().get(
            "/private/", HTTP_AUTHORIZATION="Bearer valid-token",
        )
        FirebaseIdentityAuthentication().authenticate(request)
        session = IdentitySession.objects.get()
        self.assertTrue(session.mfa_verified)
        self.assertEqual(session.second_factor_type, "phone")

    @patch("apps.identity.authentication.firebase_auth.verify_id_token")
    @patch("apps.identity.authentication.FirebaseAdminAppFactory.get_app")
    def test_unknown_second_factor_is_not_trusted(self, get_app, verify_token):
        get_app.return_value = object()
        verify_token.return_value = {
            "uid": "mfa-unknown-subject",
            "auth_time": 1_798_000_003,
            "firebase": {"sign_in_second_factor": "custom-unreviewed"},
        }
        request = APIRequestFactory().get(
            "/private/", HTTP_AUTHORIZATION="Bearer valid-token",
        )
        FirebaseIdentityAuthentication().authenticate(request)
        session = IdentitySession.objects.get()
        self.assertFalse(session.mfa_verified)


class VerifiedMFAPermissionTests(TestCase):
    def test_permission_requires_server_verified_request_context(self):
        class User:
            is_authenticated = True

        class Request:
            user = User()
            nexora_mfa_verified = True

        self.assertTrue(VerifiedMFARequired().has_permission(Request(), None))
        Request.nexora_mfa_verified = False
        self.assertFalse(VerifiedMFARequired().has_permission(Request(), None))
        del Request.nexora_mfa_verified
        Request.mfa_verified = True
        self.assertFalse(VerifiedMFARequired().has_permission(Request(), None))
