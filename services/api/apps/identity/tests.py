from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from .authentication import FirebaseIdentityAuthentication

from .models import IdentityProviderAccount, NexoraUser
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
