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
