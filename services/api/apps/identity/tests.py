from django.test import TestCase

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
