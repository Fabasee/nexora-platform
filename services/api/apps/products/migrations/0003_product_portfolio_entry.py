import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0002_product_plans_and_subscriptions"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductPortfolioEntry",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("key", models.SlugField(max_length=80, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("entry_type", models.CharField(choices=[("application", "Application"), ("module", "Module"), ("platform_service", "Platform service")], max_length=24)),
                ("category", models.CharField(max_length=64)),
                ("description", models.CharField(blank=True, max_length=500)),
                ("lifecycle_status", models.CharField(choices=[("in_development", "In development"), ("planned", "Planned"), ("research", "Research"), ("proposed", "Proposed"), ("live", "Live"), ("paused", "Paused")], default="proposed", max_length=20)),
                ("decision_status", models.CharField(choices=[("confirmed", "Confirmed direction"), ("candidate", "Candidate / needs validation")], default="candidate", max_length=12)),
                ("priority", models.CharField(choices=[("core", "Core"), ("viral", "Viral growth"), ("strategic", "Strategic"), ("supporting", "Supporting"), ("future", "Future")], default="future", max_length=12)),
                ("delivery_model", models.CharField(choices=[("standalone", "Standalone application"), ("module", "Feature / module"), ("shared", "Shared platform service")], default="standalone", max_length=12)),
                ("sort_order", models.PositiveIntegerField(default=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("activation_product", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="portfolio_entries", to="products.product")),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="modules", to="products.productportfolioentry")),
            ],
            options={
                "db_table": "products_portfolio_entry",
                "ordering": ("sort_order", "name"),
            },
        ),
        migrations.AddIndex(
            model_name="productportfolioentry",
            index=models.Index(fields=["entry_type", "lifecycle_status"], name="portfolio_type_stage_idx"),
        ),
        migrations.AddIndex(
            model_name="productportfolioentry",
            index=models.Index(fields=["decision_status", "priority"], name="portfolio_decision_priority_idx"),
        ),
    ]
