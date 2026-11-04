import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("identity", "0002_securityevent"),
    ]

    operations = [
        migrations.CreateModel(
            name="IdentitySession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("authenticated_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("source_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=512)),
                ("provider_account", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="sessions",
                    to="identity.identityprovideraccount",
                )),
            ],
            options={"db_table": "identity_session", "ordering": ("-last_seen_at",)},
        ),
        migrations.AddConstraint(
            model_name="identitysession",
            constraint=models.UniqueConstraint(
                fields=("provider_account", "authenticated_at"),
                name="identity_session_auth_time_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="identitysession",
            index=models.Index(
                fields=["provider_account", "revoked_at"],
                name="identity_session_active_idx",
            ),
        ),
    ]
