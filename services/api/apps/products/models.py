import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Product(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        MAINTENANCE = "maintenance", "Maintenance"
        RETIRED = "retired", "Retired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=280, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products_product"
        ordering = ("name",)

    def __str__(self):
        return self.key


class ProductMembership(models.Model):
    class Status(models.TextChoices):
        INVITED = "invited", "Invited"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        REVOKED = "revoked", "Revoked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="product_memberships")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="memberships")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.INVITED)
    joined_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products_membership"
        constraints = [
            models.UniqueConstraint(fields=("user", "product"), name="products_user_product_uniq"),
        ]
        indexes = [
            models.Index(fields=("user", "status"), name="products_user_status_idx"),
            models.Index(fields=("product", "status"), name="products_product_status_idx"),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.product.key}"


class Entitlement(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        REVOKED = "revoked", "Revoked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="entitlements")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="entitlements")
    feature_key = models.SlugField(max_length=80)
    scope = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "products_entitlement"
        indexes = [
            models.Index(fields=("user", "product", "feature_key", "status"), name="products_entitlement_lookup_idx"),
        ]

    def __str__(self):
        return f"{self.product.key}:{self.feature_key}:{self.user_id}"
