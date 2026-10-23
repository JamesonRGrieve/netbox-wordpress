# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_wordpress --check --dry-run
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_wordpress", "0003_wordpressmuplugin"),
    ]
    operations = [
        migrations.AddField(
            model_name="wordpressplugin",
            name="repository",
            field=models.CharField(blank=True, max_length=200, validators=[django.core.validators.RegexValidator("^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$", "<Org>/<repo>, e.g. TheBraCoach/bracoach-square-sync.")]),
        ),
        migrations.AddField(
            model_name="wordpressplugin",
            name="commit",
            field=models.CharField(blank=True, max_length=40, validators=[django.core.validators.RegexValidator("^[0-9a-f]{40}$", "A full lowercase 40-hex commit id.")]),
        ),
    ]
