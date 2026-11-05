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


class ProductPlan(models.Model):
    class Tier(models.TextChoices):
        FREE = "free", "Free"
        PRO = "pro", "Pro"

    class BillingInterval(models.TextChoices):
        NONE = "none", "No billing"
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="plans")
    key = models.SlugField(max_length=40)
    name = models.CharField(max_length=80)
    tier = models.CharField(max_length=12, choices=Tier.choices)
    price_minor = models.PositiveBigIntegerField(default=0)
    currency = models.CharField(max_length=3, default="IDR")
    billing_interval = models.CharField(max_length=12, choices=BillingInterval.choices, default=BillingInterval.NONE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products_plan"
        constraints = [
            models.UniqueConstraint(fields=("product", "key"), name="products_plan_product_key_uniq"),
        ]
        indexes = [models.Index(fields=("product", "tier", "is_active"), name="products_plan_tier_idx")]

    def __str__(self):
        return f"{self.product.key}:{self.key}"


class PlanFeature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(ProductPlan, on_delete=models.CASCADE, related_name="features")
    feature_key = models.SlugField(max_length=80)
    scope = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "products_plan_feature"
        constraints = [
            models.UniqueConstraint(fields=("plan", "feature_key"), name="products_plan_feature_uniq"),
        ]

    def __str__(self):
        return f"{self.plan}:{self.feature_key}"


class ProductSubscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="product_subscriptions")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="subscriptions")
    plan = models.ForeignKey(ProductPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateTimeField(default=timezone.now)
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products_subscription"
        constraints = [
            models.UniqueConstraint(fields=("user", "product"), name="products_user_product_sub_uniq"),
        ]
        indexes = [
            models.Index(fields=("user", "status"), name="products_sub_user_status_idx"),
            models.Index(fields=("product", "plan", "status"), name="products_sub_plan_status_idx"),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.product.key}:{self.plan.key}"


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
            models.Index(fields=("user", "product", "feature_key", "status"), name="prod_entitlement_lookup_idx"),
        ]

    def __str__(self):
        return f"{self.product.key}:{self.feature_key}:{self.user_id}"


class ProductPortfolioEntry(models.Model):
    """Governed portfolio record; not every entry is an activatable product."""

    class EntryType(models.TextChoices):
        APPLICATION = "application", "Application"
        MODULE = "module", "Module"
        PLATFORM_SERVICE = "platform_service", "Platform service"

    class LifecycleStatus(models.TextChoices):
        IN_DEVELOPMENT = "in_development", "In development"
        PLANNED = "planned", "Planned"
        RESEARCH = "research", "Research"
        PROPOSED = "proposed", "Proposed"
        LIVE = "live", "Live"
        PAUSED = "paused", "Paused"

    class DecisionStatus(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed direction"
        CANDIDATE = "candidate", "Candidate / needs validation"

    class Priority(models.TextChoices):
        CORE = "core", "Core"
        VIRAL = "viral", "Viral growth"
        STRATEGIC = "strategic", "Strategic"
        SUPPORTING = "supporting", "Supporting"
        FUTURE = "future", "Future"

    class DeliveryModel(models.TextChoices):
        STANDALONE = "standalone", "Standalone application"
        MODULE = "module", "Feature / module"
        SHARED = "shared", "Shared platform service"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    entry_type = models.CharField(max_length=24, choices=EntryType.choices)
    category = models.CharField(max_length=64)
    description = models.CharField(max_length=500, blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT,
        related_name="modules",
    )
    lifecycle_status = models.CharField(
        max_length=20, choices=LifecycleStatus.choices,
        default=LifecycleStatus.PROPOSED,
    )
    decision_status = models.CharField(
        max_length=12, choices=DecisionStatus.choices,
        default=DecisionStatus.CANDIDATE,
    )
    priority = models.CharField(
        max_length=12, choices=Priority.choices, default=Priority.FUTURE,
    )
    delivery_model = models.CharField(
        max_length=12, choices=DeliveryModel.choices,
        default=DeliveryModel.STANDALONE,
    )
    activation_product = models.ForeignKey(
        Product, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="portfolio_entries",
    )
    sort_order = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products_portfolio_entry"
        ordering = ("sort_order", "name")
        indexes = [
            models.Index(fields=("entry_type", "lifecycle_status"), name="portfolio_type_stage_idx"),
            models.Index(fields=("decision_status", "priority"), name="portfolio_decision_idx"),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError({"parent": "A portfolio entry cannot be its own parent."})
        if self.entry_type == self.EntryType.MODULE and not self.parent_id:
            raise ValidationError({"parent": "A module must belong to a parent application."})
        if self.parent_id and self.parent.entry_type != self.EntryType.APPLICATION:
            raise ValidationError({"parent": "Modules must belong directly to a parent application."})
        if self.entry_type != self.EntryType.MODULE and self.parent_id:
            raise ValidationError({"parent": "Only modules can have a parent portfolio entry."})

    def __str__(self):
        return f"{self.key} ({self.lifecycle_status})"
