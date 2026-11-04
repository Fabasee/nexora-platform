from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from .authentication import FirebaseIdentityAuthentication

from .models import IdentityProviderAccount, IdentitySession, NexoraUser, SecurityEvent
from .services import IdentityAccessDenied, IdentityService, VerifiedIdentity


class IdentityServiceTests(TestCase):
    def test_first_login_creates_one_canonical_user_and_provider_binding(self):
        identity = VerifiedIdentity(provider="firebase", subject="firebase-user-001")

        first = IdentityService.resolve_verified_identity(identity)
        second = IdentityService.resolve_verified_identity(identity)

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(NexoraUser.objects.count(), 1)
        self.assertEqual(IdentityProviderAccount.objects.count(), 1)
        self.assertFalse(first.has_usable_password())

    def test_provider_key_is_normalized_before_lookup(self):
        first = IdentityService.resolve_verified_identity(
            VerifiedIdentity(provider="Firebase", subject="firebase-user-002")
        )
        second = IdentityService.resolve_verified_identity(
            VerifiedIdentity(provider=" firebase ", subject="firebase-user-002")
        )

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(IdentityProviderAccount.objects.get().provider, "firebase")

    def test_suspended_account_cannot_authenticate(self):
        user = IdentityService.resolve_verified_identity(
            VerifiedIdentity(provider="firebase", subject="firebase-user-003")
        )
        user.status = NexoraUser.Status.SUSPENDED
        user.save(update_fields=("status", "updated_at"))

        with self.assertRaises(IdentityAccessDenied):
            IdentityService.resolve_verified_identity(
                VerifiedIdentity(provider="firebase", subject="firebase-user-003")
            )


class FirebaseIdentityAuthenticationTests(TestCase):
    @patch("apps.identity.authentication.firebase_auth.verify_id_token")
    @patch("apps.identity.authentication.FirebaseAdminAppFactory.get_app")
    def test_verified_firebase_token_resolves_internal_identity(self, get_app, verify_token):
        get_app.return_value = object()
        verify_token.return_value = {
            "uid": "firebase-auth-subject",
            "auth_time": 1_798_000_000,
        }
        request = APIRequestFactory().get(
            "/api/v1/private/",
            HTTP_AUTHORIZATION="Bearer valid-token",
        )

        user, credentials = FirebaseIdentityAuthentication().authenticate(request)

        self.assertIsNone(credentials)
        self.assertTrue(user.is_active)
        self.assertEqual(user.provider_accounts.get().provider_subject, "firebase-auth-subject")
        verify_token.assert_called_once_with(
            "valid-token",
            app=get_app.return_value,
            check_revoked=True,
        )
        # Reusing the same Firebase auth_time across API requests must not
        # create a new "login" event for every request.
        FirebaseIdentityAuthentication().authenticate(request)
        self.assertEqual(
            SecurityEvent.objects.filter(
                user=user,
                event_type=SecurityEvent.EventType.AUTHENTICATED,
            ).count(),
            1,
        )

    def test_non_bearer_authorization_is_not_claimed(self):
        request = APIRequestFactory().get(
            "/api/v1/private/",
            HTTP_AUTHORIZATION="Basic dXNlcjpwYXNz",
        )

        self.assertIsNone(FirebaseIdentityAuthentication().authenticate(request))

from rest_framework.test import APIClient


class CurrentAccountApiTests(TestCase):
    def setUp(self):
        self.user = NexoraUser.objects.create_user()
        IdentityProviderAccount.objects.create(
            user=self.user,
            provider="firebase",
            provider_subject="firebase-account-subject",
        )
        self.client = APIClient()

    def test_current_account_requires_verified_identity(self):
        response = self.client.get("/api/v1/account/me/")
        self.assertEqual(response.status_code, 401)

    def test_current_account_returns_internal_id_and_provider_without_subject(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/account/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(self.user.pk))
        self.assertEqual(response.data["status"], "active")
        self.assertEqual(response.data["providers"][0]["provider"], "firebase")
        self.assertNotIn("provider_subject", response.data["providers"][0])



class SecurityEventApiTests(TestCase):
    def setUp(self):
        self.user = NexoraUser.objects.create_user()
        self.other_user = NexoraUser.objects.create_user()
        self.client = APIClient()

    def test_security_event_history_requires_authentication(self):
        response = self.client.get("/api/v1/account/security-events/")
        self.assertEqual(response.status_code, 401)

    def test_security_event_history_is_scoped_to_current_user(self):
        own_event = SecurityEvent.objects.create(
            user=self.user,
            event_type=SecurityEvent.EventType.AUTHENTICATED,
            provider="firebase",
            source_ip="192.0.2.10",
            user_agent="Nexora mobile test",
        )
        SecurityEvent.objects.create(
            user=self.other_user,
            event_type=SecurityEvent.EventType.AUTHENTICATED,
            provider="firebase",
            source_ip="192.0.2.20",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/v1/account/security-events/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], str(own_event.pk))
        self.assertEqual(response.data["results"][0]["source_ip"], "192.0.2.10")
        self.assertNotIn("dedupe_key", response.data["results"][0])
        self.assertNotIn("request_id", response.data["results"][0])

    def test_security_event_history_is_limited_to_latest_fifty(self):
        for index in range(55):
            SecurityEvent.objects.create(
                user=self.user,
                event_type=SecurityEvent.EventType.ACCOUNT_VIEWED,
                request_id=str(index),
            )
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/v1/account/security-events/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 50)



class IdentitySessionApiTests(TestCase):
    def setUp(self):
        self.user = NexoraUser.objects.create_user()
        self.other_user = NexoraUser.objects.create_user()
        self.provider = IdentityProviderAccount.objects.create(
            user=self.user,
            provider="firebase",
            provider_subject="session-owner-subject",
        )
        self.session = IdentitySession.objects.create(
            provider_account=self.provider,
            authenticated_at=timezone.now(),
            last_seen_at=__import__("django.utils.timezone", fromlist=["now"]).now(),
            user_agent="Nexora test device",
        )
        self.client = APIClient()

    def test_session_inventory_is_scoped_to_authenticated_account(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/account/sessions/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.session.pk))
        self.assertFalse(response.data["results"][0]["is_current"])

    def test_user_can_revoke_own_session(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f"/api/v1/account/sessions/{self.session.pk}/revoke/",
        )

        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertIsNotNone(self.session.revoked_at)
        self.assertTrue(SecurityEvent.objects.filter(
            user=self.user,
            event_type=SecurityEvent.EventType.SESSION_REVOKED,
        ).exists())

    def test_user_cannot_revoke_another_accounts_session(self):
        other_provider = IdentityProviderAccount.objects.create(
            user=self.other_user,
            provider="firebase",
            provider_subject="other-session-subject",
        )
        other_session = IdentitySession.objects.create(
            provider_account=other_provider,
            authenticated_at=self.session.authenticated_at,
            last_seen_at=self.session.last_seen_at,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f"/api/v1/account/sessions/{other_session.pk}/revoke/",
        )

        self.assertEqual(response.status_code, 404)
        other_session.refresh_from_db()
        self.assertIsNone(other_session.revoked_at)


class RevokedIdentitySessionTests(TestCase):
    @patch("apps.identity.authentication.firebase_auth.verify_id_token")
    @patch("apps.identity.authentication.FirebaseAdminAppFactory.get_app")
    def test_revoked_session_is_rejected_even_if_firebase_token_is_valid(self, get_app, verify_token):
        get_app.return_value = object()
        verify_token.return_value = {
            "uid": "revoked-session-subject",
            "auth_time": 1_798_000_000,
        }
        request = APIRequestFactory().get(
            "/api/v1/private/",
            HTTP_AUTHORIZATION="Bearer valid-token",
        )
        authenticator = FirebaseIdentityAuthentication()
        user, _ = authenticator.authenticate(request)
        session = IdentitySession.objects.get(provider_account__user=user)
        session.revoked_at = __import__("django.utils.timezone", fromlist=["now"]).now()
        session.save(update_fields=("revoked_at",))

        with self.assertRaises(AuthenticationFailed):
            authenticator.authenticate(request)
