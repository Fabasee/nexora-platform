from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.permissions import VerifiedEmailRequired
from .models import ProductSubscription
from .services import ProductAccessService, ProductActivationError, ProductActivationService


class AccessibleProductsView(APIView):
    permission_classes = [IsAuthenticated, VerifiedEmailRequired]

    def get(self, request):
        products = ProductAccessService.list_accessible_products(request.user)
        return Response({
            "results": [
                {"key": product.key, "name": product.name, "description": product.description}
                for product in products
            ],
        })


class ProductActivationView(APIView):
    permission_classes = [IsAuthenticated, VerifiedEmailRequired]

    def post(self, request, product_key):
        try:
            membership, subscription, membership_created, subscription_created = (
                ProductActivationService.activate_free(request.user, product_key)
            )
        except ProductActivationError as exc:
            return Response(
                {"detail": str(exc), "code": "product_activation_denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        payload = {
            "product": product_key,
            "membership": membership.status,
            "subscription": {
                "id": str(subscription.pk),
                "status": subscription.status,
                "plan": subscription.plan.key,
                "plan_name": subscription.plan.name,
                "tier": subscription.plan.tier,
                "currency": subscription.plan.currency,
                "price_minor": subscription.plan.price_minor,
                "auto_renew": subscription.auto_renew,
            },
            "created": {
                "membership": membership_created,
                "subscription": subscription_created,
            },
        }
        return Response(
            payload,
            status=status.HTTP_201_CREATED if subscription_created else status.HTTP_200_OK,
        )


class ProductSubscriptionView(APIView):
    permission_classes = [IsAuthenticated, VerifiedEmailRequired]

    def get(self, request, product_key):
        subscription = ProductSubscription.objects.select_related("product", "plan").filter(
            user=request.user, product__key=product_key
        ).first()
        if subscription is None:
            return Response(
                {"detail": "This product has not been activated.", "code": "product_not_activated"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            "product": subscription.product.key,
            "status": subscription.status,
            "plan": subscription.plan.key,
            "plan_name": subscription.plan.name,
            "tier": subscription.plan.tier,
            "currency": subscription.plan.currency,
            "price_minor": subscription.plan.price_minor,
            "started_at": subscription.started_at,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "auto_renew": subscription.auto_renew,
        })


class ProductCatalogView(APIView):
    """List active products and the requesting user's own activation state."""

    permission_classes = [IsAuthenticated, VerifiedEmailRequired]

    def get(self, request):
        from .models import Product, ProductMembership

        products = Product.objects.filter(status=Product.Status.ACTIVE).order_by("name")
        memberships = {
            item.product_id: item
            for item in ProductMembership.objects.filter(user=request.user, product__in=products)
        }
        subscriptions = {
            item.product_id: item
            for item in ProductSubscription.objects.select_related("plan").filter(
                user=request.user, product__in=products
            )
        }
        results = []
        for product in products:
            membership = memberships.get(product.pk)
            subscription = subscriptions.get(product.pk)
            results.append({
                "key": product.key,
                "name": product.name,
                "description": product.description,
                "is_activated": bool(
                    membership and membership.status == ProductMembership.Status.ACTIVE
                    and subscription and subscription.status == ProductSubscription.Status.ACTIVE
                ),
                "membership_status": membership.status if membership else None,
                "subscription": ({
                    "status": subscription.status,
                    "plan": subscription.plan.key,
                    "plan_name": subscription.plan.name,
                    "tier": subscription.plan.tier,
                } if subscription else None),
            })
        return Response({"results": results})
