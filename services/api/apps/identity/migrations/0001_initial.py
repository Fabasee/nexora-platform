import uuid

import apps.identity.managers
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="NexoraUser",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("active", "Active"), ("suspended", "Suspended"), ("deactivated", "Deactivated")], default="active", max_length=16)),
                ("is_staff", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"db_table": "identity_nexora_user", "ordering": ("created_at",)},
            managers=[("objects", apps.identity.managers.NexoraUserManager())],
        ),
        migrations.CreateModel(
            name="IdentityProviderAccount",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("provider", models.CharField(max_length=32)),
                ("provider_subject", models.CharField(max_length=255)),
                ("last_authenticated_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="provider_accounts", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "identity_provider_account"},
        ),
        migrations.AddConstraint(
            model_name="identityprovideraccount",
            constraint=models.UniqueConstraint(fields=("provider", "provider_subject"), name="identity_provider_subject_uniq"),
        ),
        migrations.AddIndex(
            model_name="identityprovideraccount",
            index=models.Index(fields=["user", "provider"], name="identity_user_provider_idx"),
        ),
    ]
