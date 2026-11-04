from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("identity", "0004_identitysession_email_verified"),
    ]

    operations = [
        migrations.AlterField(
            model_name="securityevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("identity.authenticated", "Identity authenticated"),
                    ("identity.account_viewed", "Account viewed"),
                    ("identity.verification_requested", "Verification requested"),
                    ("identity.password_reset_requested", "Password reset requested"),
                    ("identity.session_revoked", "Session revoked"),
                    ("identity.email_verification_confirmed", "Email verification confirmed"),
                    ("identity.credential_changed", "Credential changed"),
                ],
                max_length=64,
            ),
        ),
    ]
