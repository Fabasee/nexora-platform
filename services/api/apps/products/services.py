from django.utils import timezone

from .models import Entitlement, Product, ProductMembership


class ProductAccessDenied(Exception):
    """Raised when a user has no active grant for a product or feature."""


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
    def assert_access(user, product_key: str, feature_key: str | None = None):
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
            return product

        now = timezone.now()
        entitlement_exists = Entitlement.objects.filter(
            user=user,
            product=product,
            feature_key=feature_key,
            status=Entitlement.Status.ACTIVE,
            starts_at__lte=now,
            revoked_at__isnull=True,
        ).filter(
            models_end_after(now)
        ).exists()
        if not entitlement_exists:
            raise ProductAccessDenied("The account does not have the required feature entitlement.")
        return product


def models_end_after(now):
    from django.db.models import Q
    return Q(ends_at__isnull=True) | Q(ends_at__gt=now)
