from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    Entitlement,
    PlanFeature,
    Product,
    ProductMembership,
    ProductPlan,
    ProductSubscription,
)


class ProductAccessDenied(Exception):
    """Raised when a user has no active grant for a product or feature."""


class ProductActivationError(Exception):
    """Raised when product activation is not allowed."""


class ProductAccessService:
    @staticmethod
    def list_accessible_products(user):
        if not user.is_active:
            return Product.objects.none()
        return Product.objects.filter(
            status=Product.Status.ACTIVE,
            memberships__user=user,
            memberships__status=ProductMembership.Status.ACTIVE,
        ).distinct()

    @staticmethod
    def assert_access(
        user,
        product_key: str,
        feature_key: str | None = None,
        required_scope: dict[str, object] | None = None,
    ):
        if not user.is_active:
            raise ProductAccessDenied("The Nexora account is not active.")

        try:
            product = Product.objects.get(key=product_key, status=Product.Status.ACTIVE)
        except Product.DoesNotExist:
            raise ProductAccessDenied("The requested product is not available.") from None

        membership_exists = ProductMembership.objects.filter(
            user=user,
            product=product,
            status=ProductMembership.Status.ACTIVE,
        ).exists()
        if not membership_exists:
            raise ProductAccessDenied("The account has no active membership in this product.")

        if feature_key is None:
            if required_scope is not None:
                raise ValueError("A required scope can only be checked with a feature key.")
            return product

        now = timezone.now()
        grants = Entitlement.objects.filter(
            user=user,
            product=product,
            feature_key=feature_key,
            status=Entitlement.Status.ACTIVE,
            starts_at__lte=now,
            revoked_at__isnull=True,
        ).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gt=now)
        ).values_list("scope", flat=True)

        if not required_scope:
            granted = any(scope == {} for scope in grants)
        else:
            granted = any(
                isinstance(scope, dict)
                and all(key in scope and scope[key] == value for key, value in required_scope.items())
                for scope in grants
            )

        if not granted:
            raise ProductAccessDenied("The account does not have the required feature entitlement.")
        return product


class ProductActivationService:
    """Idempotently grant a product's Free plan on its first explicit launch."""

    @classmethod
    @transaction.atomic
    def activate_free(cls, user, product_key: str):
        if not user.is_active:
            raise ProductActivationError("The Nexora account is not active.")

        try:
            product = Product.objects.select_for_update().get(
                key=product_key,
                status=Product.Status.ACTIVE,
            )
        except Product.DoesNotExist:
            raise ProductActivationError("The requested product is not available.") from None

        free_plan, _ = ProductPlan.objects.get_or_create(
            product=product,
            key="free",
            defaults={
                "name": "Free",
                "tier": ProductPlan.Tier.FREE,
                "price_minor": 0,
                "currency": "IDR",
                "billing_interval": ProductPlan.BillingInterval.NONE,
                "is_active": True,
            },
        )
        if (
            free_plan.tier != ProductPlan.Tier.FREE
            or free_plan.price_minor != 0
            or not free_plan.is_active
        ):
            raise ProductActivationError("The product's Free plan is not configured safely.")

        membership, membership_created = ProductMembership.objects.get_or_create(
            user=user,
            product=product,
            defaults={
                "status": ProductMembership.Status.ACTIVE,
                "joined_at": timezone.now(),
            },
        )
        if membership.status in (ProductMembership.Status.SUSPENDED, ProductMembership.Status.REVOKED):
            raise ProductActivationError("This product membership is blocked.")
        if membership.status != ProductMembership.Status.ACTIVE:
            membership.status = ProductMembership.Status.ACTIVE
            membership.joined_at = membership.joined_at or timezone.now()
            membership.save(update_fields=("status", "joined_at", "updated_at"))

        subscription, subscription_created = ProductSubscription.objects.get_or_create(
            user=user,
            product=product,
            defaults={"plan": free_plan, "status": ProductSubscription.Status.ACTIVE},
        )
        if not subscription_created and subscription.status != ProductSubscription.Status.ACTIVE:
            subscription.plan = free_plan
            subscription.status = ProductSubscription.Status.ACTIVE
            subscription.started_at = timezone.now()
            subscription.current_period_start = timezone.now()
            subscription.current_period_end = None
            subscription.auto_renew = False
            subscription.save(update_fields=(
                "plan", "status", "started_at", "current_period_start",
                "current_period_end", "auto_renew", "updated_at",
            ))

        # A repeated launch must never downgrade an existing paid subscription.
        if subscription.plan_id != free_plan.pk:
            return membership, subscription

        for feature in PlanFeature.objects.filter(plan=free_plan):
            Entitlement.objects.get_or_create(
                user=user,
                product=product,
                feature_key=feature.feature_key,
                scope=feature.scope,
                status=Entitlement.Status.ACTIVE,
                revoked_at__isnull=True,
                defaults={"starts_at": timezone.now()},
            )

        return membership, subscription
