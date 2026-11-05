import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.products.models import PortfolioAuditEvent, Product, ProductPortfolioEntry
from apps.products.portfolio_audit import save_portfolio_entry


class Command(BaseCommand):
    help = "Synchronize the governed Nexora portfolio registry from its version-controlled JSON manifest."

    def add_arguments(self, parser):
        parser.add_argument(
            "--manifest",
            default=None,
            help="Optional path to a registry JSON manifest.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and report changes without persisting them.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        default_path = Path(settings.BASE_DIR).resolve().parent.parent / (
            "docs/product-registry/master-product-registry.json"
        )
        manifest_path = Path(options["manifest"]).resolve() if options["manifest"] else default_path
        if not manifest_path.is_file():
            raise CommandError(f"Registry manifest not found: {manifest_path}")

        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Unable to read registry manifest: {exc}") from exc

        if payload.get("schema_version") != 1 or not isinstance(payload.get("entries"), list):
            raise CommandError("Unsupported or invalid registry manifest schema.")

        entries = payload["entries"]
        seen_keys = set()
        created = updated = 0

        for item in entries:
            key = item.get("key")
            if not key or key in seen_keys:
                raise CommandError(f"Missing or duplicate portfolio key: {key!r}")
            seen_keys.add(key)

            parent_key = item.pop("parent_key", None)
            activation_product_key = item.pop("activation_product_key", None)
            if parent_key and parent_key not in seen_keys:
                raise CommandError(
                    f"Parent {parent_key!r} for {key!r} must appear earlier in the manifest."
                )

            parent = ProductPortfolioEntry.objects.filter(key=parent_key).first() if parent_key else None
            if parent_key and parent is None:
                raise CommandError(f"Parent portfolio entry {parent_key!r} does not exist.")

            activation_product = None
            if activation_product_key:
                activation_product = Product.objects.filter(key=activation_product_key).first()
                if activation_product is None:
                    raise CommandError(
                        f"Activation product {activation_product_key!r} for {key!r} does not exist."
                    )

            defaults = {
                "name": item["name"],
                "entry_type": item["entry_type"],
                "category": item["category"],
                "description": item.get("description", ""),
                "parent": parent,
                "lifecycle_status": item["lifecycle_status"],
                "decision_status": item["decision_status"],
                "priority": item["priority"],
                "delivery_model": item["delivery_model"],
                "activation_product": activation_product,
                "sort_order": item.get("sort_order", 100),
            }
            entry = ProductPortfolioEntry.objects.filter(key=key).first()
            was_created = entry is None
            if entry is None:
                entry = ProductPortfolioEntry(key=key)
            for field, value in defaults.items():
                setattr(entry, field, value)
            entry, changed = save_portfolio_entry(
                entry=entry,
                source=PortfolioAuditEvent.Source.MANIFEST,
            )
            if was_created:
                created += 1
            elif changed:
                updated += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run valid: {len(entries)} entries; {created} would be created, "
                    f"{updated} would be updated."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Registry synchronized: {len(entries)} entries; "
                f"{created} created, {updated} updated. No entries were deleted."
            )
        )
