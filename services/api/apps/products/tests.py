from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.identity.models import IdentityProviderAccount, NexoraUser
from .models import (Entitlement, PlanFeature, Product, ProductMembership, ProductPlan, ProductSubscription)
from .services import (ProductAccessDenied, ProductAccessService, ProductActivationError, ProductActivationService)


class ProductAccessServiceTests(TestCase):
    def setUp(self):
        self.user = NexoraUser.objects.create_user()
        self.product = Product.objects.create(
            key="day-date",
            name="Day-Date",
            status=Product.Status.ACTIVE,
        )
        self.membership = ProductMembership.objects.create(
            user=self.user,
            product=self.product,
            status=ProductMembership.Status.ACTIVE,
        )

    def test_lists_only_products_with_active_membership(self):
        products = ProductAccessService.list_accessible_products(self.user)

        self.assertEqual(list(products.values_list("key", flat=True)), ["day-date"])

    def test_product_membership_is_required(self):
        self.membership.status = ProductMembership.Status.SUSPENDED
        self.membership.save(update_fields=("status", "updated_at"))

        with self.assertRaises(ProductAccessDenied):
            ProductAccessService.assert_access(self.user, "day-date")

    def test_product_wide_entitlement_grants_feature(self):
        Entitlement.objects.create(
            user=self.user,
            product=self.product,
            feature_key="premium-dashboard",
            scope={},
        )

        result = ProductAccessService.assert_access(
            self.user, "day-date", "premium-dashboard"
        )
        self.assertEqual(result.pk, self.product.pk)

    def test_scoped_entitlement_does_not_grant_product_wide_access(self):
        Entitlement.objects.create(
            user=self.user,
            product=self.product,
            feature_key="workspace-export",
            scope={"workspace_id": "workspace-1"},
        )

        with self.assertRaises(ProductAccessDenied):
            ProductAccessService.assert_access(self.user, "day-date", "workspace-export")

    def test_scoped_entitlement_requires_matching_scope(self):
        Entitlement.objects.create(
            user=self.user,
            product=self.product,
            feature_key="workspace-export",
            scope={"workspace_id": "workspace-1", "region": "id"},
        )

        result = ProductAccessService.assert_access(
            self.user,
            "day-date",
            "workspace-export",
            required_scope={"workspace_id": "workspace-1"},
        )
        self.assertEqual(result.pk, self.product.pk)

        with self.assertRaises(ProductAccessDenied):
            ProductAccessService.assert_access(
                self.user,
                "day-date",
                "workspace-export",
                required_scope={"workspace_id": "workspace-2"},
            )

    def test_retired_product_is_not_accessible(self):
        self.product.status = Product.Status.RETIRED
        self.product.save(update_fields=("status", "updated_at"))

        with self.assertRaises(ProductAccessDenied):
            ProductAccessService.assert_access(self.user, "day-date")


class ProductAccessApiTests(TestCase):
    def setUp(self):
        self.user = NexoraUser.objects.create_user()
        self.product = Product.objects.create(key="dignity", name="Dignity")
        IdentityProviderAccount.objects.create(
            user=self.user,
            provider="firebase",
            provider_subject="product-api-user",
        )
        ProductMembership.objects.create(
            user=self.user,
            product=self.product,
            status=ProductMembership.Status.ACTIVE,
        )
        self.client = APIClient()

    def test_product_catalog_requires_authentication(self):
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_without_verified_email_is_denied(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/v1/products/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"].code, "email_verification_required")

    @patch("apps.identity.authentication.firebase_auth.verify_id_token")
    @patch("apps.identity.authentication.FirebaseAdminAppFactory.get_app")
    def test_verified_firebase_identity_can_access_product_catalog(self, get_app, verify_token):
        get_app.return_value = object()
        verify_token.return_value = {
            "uid": "product-api-user",
            "auth_time": 1_798_000_000,
            "email_verified": True,
        }

        response = self.client.get(
            "/api/v1/products/",
            HTTP_AUTHORIZATION="Bearer valid-token",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [
            {"key": "dignity", "name": "Dignity", "description": ""},
        ])

    @patch("apps.identity.authentication.firebase_auth.verify_id_token")
    @patch("apps.identity.authentication.FirebaseAdminAppFactory.get_app")
    def test_unverified_firebase_identity_cannot_access_product_catalog(self, get_app, verify_token):
        get_app.return_value = object()
        verify_token.return_value = {
            "uid": "product-api-user",
            "auth_time": 1_798_000_000,
            "email_verified": False,
        }

        response = self.client.get(
            "/api/v1/products/",
            HTTP_AUTHORIZATION="Bearer valid-token",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"].code, "email_verification_required")



class ProductActivationServiceTests(TestCase):
    def setUp(self):
        self.user = NexoraUser.objects.create_user()
        self.product = Product.objects.create(key="day-date", name="Day-Date")

    def test_first_launch_grants_free_plan_and_membership(self):
        membership, subscription, membership_created, subscription_created = (
            ProductActivationService.activate_free(self.user, "day-date")
        )

        self.assertEqual(membership.status, ProductMembership.Status.ACTIVE)
        self.assertEqual(subscription.status, ProductSubscription.Status.ACTIVE)
        self.assertEqual(subscription.plan.key, "free")
        self.assertEqual(subscription.plan.tier, ProductPlan.Tier.FREE)
        self.assertEqual(subscription.plan.price_minor, 0)
        self.assertTrue(membership_created)
        self.assertTrue(subscription_created)

    def test_repeated_launch_is_idempotent(self):
        first = ProductActivationService.activate_free(self.user, "day-date")
        second = ProductActivationService.activate_free(self.user, "day-date")

        self.assertEqual(first[0].pk, second[0].pk)
        self.assertEqual(first[1].pk, second[1].pk)
        self.assertEqual(ProductMembership.objects.count(), 1)
        self.assertEqual(ProductSubscription.objects.count(), 1)
        self.assertFalse(second[2])
        self.assertFalse(second[3])

    def test_free_plan_features_create_entitlements(self):
        plan = ProductPlan.objects.create(
            product=self.product,
            key="free",
            name="Free",
            tier=ProductPlan.Tier.FREE,
            price_minor=0,
        )
        PlanFeature.objects.create(plan=plan, feature_key="basic-profile")

        ProductActivationService.activate_free(self.user, "day-date")

        self.assertTrue(Entitlement.objects.filter(
            user=self.user,
            product=self.product,
            feature_key="basic-profile",
            status=Entitlement.Status.ACTIVE,
        ).exists())

    def test_repeated_activation_does_not_downgrade_pro(self):
        pro = ProductPlan.objects.create(
            product=self.product,
            key="pro",
            name="Pro",
            tier=ProductPlan.Tier.PRO,
            price_minor=99000,
            billing_interval=ProductPlan.BillingInterval.MONTHLY,
        )
        ProductSubscription.objects.create(
            user=self.user,
            product=self.product,
            plan=pro,
            status=ProductSubscription.Status.ACTIVE,
        )

        _, subscription, _, created = ProductActivationService.activate_free(
            self.user, "day-date"
        )

        self.assertFalse(created)
        self.assertEqual(subscription.plan.key, "pro")

    def test_suspended_membership_cannot_be_reactivated_by_free_activation(self):
        ProductMembership.objects.create(
            user=self.user,
            product=self.product,
            status=ProductMembership.Status.SUSPENDED,
        )

        with self.assertRaises(ProductActivationError):
            ProductActivationService.activate_free(self.user, "day-date")

    def test_inactive_product_cannot_be_activated(self):
        self.product.status = Product.Status.MAINTENANCE
        self.product.save(update_fields=("status", "updated_at"))

        with self.assertRaises(ProductActivationError):
            ProductActivationService.activate_free(self.user, "day-date")


class ProductActivationApiTests(TestCase):
    def setUp(self):
        self.user = NexoraUser.objects.create_user()
        self.product = Product.objects.create(key="dignity", name="Dignity")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("apps.identity.permissions.VerifiedEmailRequired.has_permission", return_value=True)
    def test_authenticated_user_can_activate_free_product(self, _permission):
        response = self.client.post("/api/v1/products/dignity/activate/")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["subscription"]["plan"], "free")
        self.assertEqual(response.data["membership"], "active")

    @patch("apps.identity.permissions.VerifiedEmailRequired.has_permission", return_value=True)
    def test_second_activation_is_successful_and_idempotent(self, _permission):
        first = self.client.post("/api/v1/products/dignity/activate/")
        second = self.client.post("/api/v1/products/dignity/activate/")

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(ProductSubscription.objects.count(), 1)

    @patch("apps.identity.permissions.VerifiedEmailRequired.has_permission", return_value=True)
    def test_user_can_read_own_subscription_only(self, _permission):
        self.client.post("/api/v1/products/dignity/activate/")
        response = self.client.get("/api/v1/products/dignity/subscription/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["plan"], "free")
        self.assertEqual(response.data["product"], "dignity")
