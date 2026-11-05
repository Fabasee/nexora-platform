from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from .models import ProductPortfolioEntry


class ProductPortfolioRegistryTests(TestCase):
    @property
    def manifest_path(self):
        repository_root = Path(__file__).resolve().parents[4]
        return repository_root / "docs/product-registry/master-product-registry.json"

    def test_manifest_contains_confirmed_products_and_candidate_viral_modules(self):
        output = StringIO()
        call_command(
            "sync_product_registry",
            manifest=str(self.manifest_path),
            stdout=output,
        )

        self.assertEqual(ProductPortfolioEntry.objects.count(), 44)
        self.assertTrue(
            ProductPortfolioEntry.objects.filter(
                key="day-date",
                decision_status=ProductPortfolioEntry.DecisionStatus.CONFIRMED,
                lifecycle_status=ProductPortfolioEntry.LifecycleStatus.IN_DEVELOPMENT,
            ).exists()
        )
        self.assertTrue(
            ProductPortfolioEntry.objects.filter(
                key="social-pulse",
                entry_type=ProductPortfolioEntry.EntryType.MODULE,
                decision_status=ProductPortfolioEntry.DecisionStatus.CANDIDATE,
                parent__key="nexora-social",
            ).exists()
        )
        self.assertTrue(
            ProductPortfolioEntry.objects.filter(
                key="finance-accounting",
                parent__key="nexora-finance",
            ).exists()
        )

    def test_sync_is_idempotent_and_does_not_delete_unlisted_entries(self):
        call_command("sync_product_registry", manifest=str(self.manifest_path), stdout=StringIO())
        sentinel = ProductPortfolioEntry.objects.create(
            key="local-admin-entry",
            name="Local admin entry",
            entry_type=ProductPortfolioEntry.EntryType.PLATFORM_SERVICE,
            category="Local",
            lifecycle_status=ProductPortfolioEntry.LifecycleStatus.PROPOSED,
            decision_status=ProductPortfolioEntry.DecisionStatus.CANDIDATE,
            priority=ProductPortfolioEntry.Priority.FUTURE,
            delivery_model=ProductPortfolioEntry.DeliveryModel.SHARED,
        )

        call_command("sync_product_registry", manifest=str(self.manifest_path), stdout=StringIO())

        self.assertEqual(ProductPortfolioEntry.objects.count(), 45)
        self.assertTrue(ProductPortfolioEntry.objects.filter(pk=sentinel.pk).exists())

    def test_dry_run_validates_without_persisting(self):
        output = StringIO()

        call_command(
            "sync_product_registry",
            manifest=str(self.manifest_path),
            dry_run=True,
            stdout=output,
        )

        self.assertEqual(ProductPortfolioEntry.objects.count(), 0)
        self.assertIn("Dry run valid: 44 entries", output.getvalue())

    def test_manifest_requires_parent_before_child(self):
        import json
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(
                json.dumps({
                    "schema_version": 1,
                    "entries": [{
                        "key": "child",
                        "name": "Child",
                        "entry_type": "module",
                        "category": "Test",
                        "parent_key": "missing-parent",
                        "lifecycle_status": "proposed",
                        "decision_status": "candidate",
                        "priority": "future",
                        "delivery_model": "module",
                    }],
                }),
                encoding="utf-8",
            )
            with self.assertRaises(CommandError):
                call_command("sync_product_registry", manifest=str(path), stdout=StringIO())

        self.assertEqual(ProductPortfolioEntry.objects.count(), 0)
