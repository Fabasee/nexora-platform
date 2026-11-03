import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("identity", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("key", models.SlugField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("description", models.CharField(blank=True, max_length=280)),
                ("status", models.CharField(choices=[("active", "Active"), ("maintenance", "Maintenance"), ("retired", "Retired")], default="active", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "products_product", "ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="Entitlement",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("feature_key", models.SlugField(max_length=80)),
                ("scope", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(choices=[("active", "Active"), ("revoked", "Revoked")], default="active", max_length=16)),
                ("starts_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="entitlements", to="products.product")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="entitlements", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "products_entitlement"},
        ),
        migrations.CreateModel(
            name="ProductMembership",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("invited", "Invited"), ("active", "Active"), ("suspended", "Suspended"), ("revoked", "Revoked")], default="invited", max_length=16)),
                ("joined_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="memberships", to="products.product")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="product_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "products_membership"},
        ),
        migrations.AddConstraint(
            model_name="productmembership",
            constraint=models.UniqueConstraint(fields=("user", "product"), name="products_user_product_uniq"),
        ),
        migrations.AddIndex(
            model_name="productmembership",
            index=models.Index(fields=["user", "status"], name="products_user_status_idx"),
        ),
        migrations.AddIndex(
            model_name="productmembership",
            index=models.Index(fields=["product", "status"], name="products_product_status_idx"),
        ),
        migrations.AddIndex(
            model_name="entitlement",
            index=models.Index(fields=["user", "product", "feature_key", "status"], name="products_entitlement_lookup_idx"),
        ),
    ]
