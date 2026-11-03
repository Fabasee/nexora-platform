from dataclasses import dataclass
from datetime import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import IdentityProviderAccount, NexoraUser


class IdentityAccessDenied(Exception):
    """Raised when a verified provider identity maps to a blocked account."""


@dataclass(frozen=True, slots=True)
class VerifiedIdentity:
    """Provider-neutral identity data produced only after token verification."""

    provider: str
    subject: str
    authenticated_at: datetime | None = None


class IdentityService:
    """Resolve verified external identities to immutable Nexora UUIDs."""

    @classmethod
    def resolve_verified_identity(cls, identity: VerifiedIdentity) -> NexoraUser:
        provider = identity.provider.strip().lower()
        subject = identity.subject.strip()
        if not provider or not subject:
            raise ValueError("A provider and stable provider subject are required.")

        account = (
            IdentityProviderAccount.objects.select_related("user")
            .filter(provider=provider, provider_subject=subject)
            .first()
        )
        if account is None:
            try:
                with transaction.atomic():
                    user = NexoraUser.objects.create_user()
                    account = IdentityProviderAccount.objects.create(
                        user=user,
                        provider=provider,
                        provider_subject=subject,
                        last_authenticated_at=identity.authenticated_at or timezone.now(),
                    )
            except IntegrityError:
                # A concurrent first login may have won the unique provider-subject race.
                account = (
                    IdentityProviderAccount.objects.select_related("user")
                    .get(provider=provider, provider_subject=subject)
                )
        else:
            account.last_authenticated_at = identity.authenticated_at or timezone.now()
            account.save(update_fields=("last_authenticated_at", "updated_at"))

        if not account.user.is_active:
            raise IdentityAccessDenied("This Nexora account is not active.")
        return account.user
