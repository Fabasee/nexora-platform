from django.test import TestCase
from rest_framework.test import APIClient

from apps.identity.models import NexoraUser
from .models import Product, ProductMembership, ProductPlan, ProductSubscription


class ProductCatalogApiTests(TestCase):
    def setUp(self):
        self.user = NexoraUser.objects.create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.active = Product.objects.create(key="day-date", name="Day-Date")
        self.maintenance = Product.objects.create(
            key="future-app", name="Future App", status=Product.Status.MAINTENANCE
        )

    def test_catalog_includes_active_products_and_account_specific_state(self):
        response = self.client.get("/api/v1/products/catalog/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0], {
            "key": "day-date",
            "name": "Day-Date",
            "description": "",
            "is_activated": False,
            "membership_status": None,
            "subscription": None,
        })

    def test_catalog_reports_active_membership_and_subscription(self):
        plan = ProductPlan.objects.create(
            product=self.active,
            key="free",
            name="Free",
            tier=ProductPlan.Tier.FREE,
            price_minor=0,
        )
        ProductMembership.objects.create(
            user=self.user,
            product=self.active,
            status=ProductMembership.Status.ACTIVE,
        )
        ProductSubscription.objects.create(
            user=self.user,
            product=self.active,
            plan=plan,
            status=ProductSubscription.Status.ACTIVE,
        )

        response = self.client.get("/api/v1/products/catalog/")

        self.assertTrue(response.data["results"][0]["is_activated"])
        self.assertEqual(response.data["results"][0]["subscription"]["tier"], "free")

    def test_catalog_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get("/api/v1/products/catalog/")

        self.assertEqual(response.status_code, 401)
