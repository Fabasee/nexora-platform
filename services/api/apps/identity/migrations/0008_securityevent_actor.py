import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("identity", "0007_identitysession_mfa_verified_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="securityevent",
            name="actor",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="security_actions", to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
