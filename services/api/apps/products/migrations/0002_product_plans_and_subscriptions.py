import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductPlan",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("key", models.SlugField(max_length=40)),
                ("name", models.CharField(max_length=80)),
                ("tier", models.CharField(choices=[("free", "Free"), ("pro", "Pro")], max_length=12)),
                ("price_minor", models.PositiveBigIntegerField(default=0)),
                ("currency", models.CharField(default="IDR", max_length=3)),
                ("billing_interval", models.CharField(choices=[("none", "No billing"), ("monthly", "Monthly"), ("yearly", "Yearly")], default="none", max_length=12)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="plans", to="products.product")),
            ],
            options={"db_table": "products_plan"},
        ),
        migrations.CreateModel(
            name="PlanFeature",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("feature_key", models.SlugField(max_length=80)),
                ("scope", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="features", to="products.productplan")),
            ],
            options={"db_table": "products_plan_feature"},
        ),
        migrations.CreateModel(
            name="ProductSubscription",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("active", "Active"), ("cancelled", "Cancelled"), ("expired", "Expired")], default="active", max_length=12)),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("current_period_start", models.DateTimeField(default=django.utils.timezone.now)),
                ("current_period_end", models.DateTimeField(blank=True, null=True)),
                ("auto_renew", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="subscriptions", to="products.productplan")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="subscriptions", to="products.product")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="product_subscriptions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "products_subscription"},
        ),
        migrations.AddConstraint(
            model_name="productplan",
            constraint=models.UniqueConstraint(fields=("product", "key"), name="products_plan_product_key_uniq"),
        ),
        migrations.AddIndex(
            model_name="productplan",
            index=models.Index(fields=["product", "tier", "is_active"], name="products_plan_tier_idx"),
        ),
        migrations.AddConstraint(
            model_name="planfeature",
            constraint=models.UniqueConstraint(fields=("plan", "feature_key"), name="products_plan_feature_uniq"),
        ),
        migrations.AddConstraint(
            model_name="productsubscription",
            constraint=models.UniqueConstraint(fields=("user", "product"), name="products_user_product_sub_uniq"),
        ),
        migrations.AddIndex(
            model_name="productsubscription",
            index=models.Index(fields=["user", "status"], name="products_sub_user_status_idx"),
        ),
        migrations.AddIndex(
            model_name="productsubscription",
            index=models.Index(fields=["product", "plan", "status"], name="products_sub_plan_status_idx"),
        ),
    ]
