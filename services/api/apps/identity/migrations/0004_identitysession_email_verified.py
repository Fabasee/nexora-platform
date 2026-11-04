from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("identity", "0003_identitysession"),
    ]

    operations = [
        migrations.AddField(
            model_name="identitysession",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
    ]
