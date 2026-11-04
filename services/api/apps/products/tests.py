from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.identity.models import IdentityProviderAccount, NexoraUser
from .models import Entitlement, Product, ProductMembership
from .services import ProductAccessDenied, ProductAccessService


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
