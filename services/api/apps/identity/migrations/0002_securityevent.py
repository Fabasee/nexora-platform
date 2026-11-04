import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("identity", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SecurityEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(choices=[
                    ("identity.authenticated", "Identity authenticated"),
                    ("identity.account_viewed", "Account viewed"),
                    ("identity.verification_requested", "Verification requested"),
                    ("identity.password_reset_requested", "Password reset requested"),
                    ("identity.session_revoked", "Session revoked"),
                    ("identity.credential_changed", "Credential changed"),
                ], max_length=64)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("provider", models.CharField(blank=True, max_length=32)),
                ("source_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=512)),
                ("request_id", models.CharField(blank=True, max_length=128)),
                ("dedupe_key", models.CharField(blank=True, max_length=64, null=True, unique=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="security_events", to="identity.nexorauser")),
            ],
            options={"db_table": "identity_security_event", "ordering": ("-occurred_at",)},
        ),
        migrations.AddIndex(
            model_name="securityevent",
            index=models.Index(fields=["user", "-occurred_at"], name="identity_event_user_time_idx"),
        ),
        migrations.AddIndex(
            model_name="securityevent",
            index=models.Index(fields=["event_type", "-occurred_at"], name="identity_event_type_time_idx"),
        ),
    ]
