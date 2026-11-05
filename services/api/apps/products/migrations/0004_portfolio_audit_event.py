import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0003_product_portfolio_entry"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PortfolioAuditEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("entry_key", models.SlugField(db_index=True, max_length=80)),
                ("entry_name", models.CharField(max_length=120)),
                ("action", models.CharField(choices=[("created", "Created"), ("updated", "Updated")], max_length=12)),
                ("source", models.CharField(choices=[("admin", "Django Admin"), ("manifest", "Manifest synchronization")], max_length=12)),
                ("actor_label", models.CharField(blank=True, max_length=160)),
                ("changes", models.JSONField(default=dict)),
                ("occurred_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="portfolio_audit_events", to=settings.AUTH_USER_MODEL)),
                ("entry", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_events", to="products.productportfolioentry")),
            ],
            options={
                "db_table": "products_portfolio_audit_event",
                "ordering": ("-occurred_at", "-id"),
            },
        ),
        migrations.AddIndex(
            model_name="portfolioauditevent",
            index=models.Index(fields=["entry_key", "-occurred_at"], name="portfolio_audit_entry_idx"),
        ),
        migrations.AddIndex(
            model_name="portfolioauditevent",
            index=models.Index(fields=["source", "-occurred_at"], name="portfolio_audit_source_idx"),
        ),
    ]
