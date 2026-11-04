import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from .managers import NexoraUserManager


class NexoraUser(AbstractBaseUser, PermissionsMixin):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        DEACTIVATED = "deactivated", "Deactivated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = NexoraUserManager()

    USERNAME_FIELD = "id"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "identity_nexora_user"
        ordering = ("created_at",)

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    def __str__(self):
        return str(self.pk)


class IdentityProviderAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        NexoraUser,
        on_delete=models.PROTECT,
        related_name="provider_accounts",
    )
    provider = models.CharField(max_length=32)
    provider_subject = models.CharField(max_length=255)
    last_authenticated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "identity_provider_account"
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "provider_subject"),
                name="identity_provider_subject_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=("user", "provider"), name="identity_user_provider_idx"),
        ]

    def __str__(self):
        return f"{self.provider}:{self.provider_subject}"


class SecurityEvent(models.Model):
    class EventType(models.TextChoices):
        AUTHENTICATED = "identity.authenticated", "Identity authenticated"
        ACCOUNT_VIEWED = "identity.account_viewed", "Account viewed"
        VERIFICATION_REQUESTED = "identity.verification_requested", "Verification requested"
        PASSWORD_RESET_REQUESTED = "identity.password_reset_requested", "Password reset requested"
        SESSION_REVOKED = "identity.session_revoked", "Session revoked"
        EMAIL_VERIFICATION_CONFIRMED = "identity.email_verification_confirmed", "Email verification confirmed"
        CREDENTIAL_CHANGED = "identity.credential_changed", "Credential changed"
        AUTH_CONTEXT_CHANGED = "identity.auth_context_changed", "Authentication context changed"
        MFA_AUTHENTICATED = "identity.mfa_authenticated", "Multi-factor authentication completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        NexoraUser,
        on_delete=models.PROTECT,
        related_name="security_events",
    )
    event_type = models.CharField(max_length=64, choices=EventType.choices)
    occurred_at = models.DateTimeField(auto_now_add=True)
    provider = models.CharField(max_length=32, blank=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    request_id = models.CharField(max_length=128, blank=True)
    dedupe_key = models.CharField(max_length=64, unique=True, null=True, blank=True)

    class Meta:
        db_table = "identity_security_event"
        ordering = ("-occurred_at",)
        indexes = [
            models.Index(fields=("user", "-occurred_at"), name="identity_event_user_time_idx"),
            models.Index(fields=("event_type", "-occurred_at"), name="identity_event_type_time_idx"),
        ]

    def __str__(self):
        return f"{self.event_type}:{self.user_id}"


class IdentitySession(models.Model):
    """Server-side session keyed to a verified provider authentication time."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider_account = models.ForeignKey(
        IdentityProviderAccount,
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    authenticated_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    mfa_verified = models.BooleanField(default=False)
    second_factor_type = models.CharField(max_length=16, blank=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)

    class Meta:
        db_table = "identity_session"
        ordering = ("-last_seen_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("provider_account", "authenticated_at"),
                name="identity_session_auth_time_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=("provider_account", "revoked_at"), name="identity_session_active_idx"),
        ]

    @property
    def is_active(self):
        return self.revoked_at is None

    def __str__(self):
        return f"{self.provider_account.user_id}:{self.id}"
