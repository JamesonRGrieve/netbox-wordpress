# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_wordpress --check --dry-run
import django.core.validators
import django.db.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("extras", "0001_initial"),
        ("netbox_wordpress", "0002_site_icon_url_wordpressoption"),
    ]
    operations = [
        migrations.CreateModel(
            name="WordPressMuPlugin",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, blank=True, null=True)),
                ("custom_field_data", models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
                ("name", models.CharField(max_length=128, validators=[django.core.validators.RegexValidator("^[A-Za-z0-9][A-Za-z0-9._-]*\\.php$", "A bare .php file name (no slashes).")])),
                ("repository", models.CharField(max_length=200, validators=[django.core.validators.RegexValidator("^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$", "<Org>/<repo>, e.g. TheBraCoach/bracoach-square-sync.")])),
                ("commit", models.CharField(max_length=40, validators=[django.core.validators.RegexValidator("^[0-9a-f]{40}$", "A full lowercase 40-hex commit id.")])),
                ("source_path", models.CharField(max_length=255, validators=[django.core.validators.RegexValidator("^(?!/)(?!(?:.*/)?\\.\\.(?:/|$)).+$", "A repo-relative path: no leading / and no .. segments.")])),
                ("sha256", models.CharField(max_length=64, validators=[django.core.validators.RegexValidator("^[0-9a-f]{64}$", "Lowercase hex sha256 (64 chars).")])),
                ("description", models.CharField(blank=True, max_length=200)),
                ("site", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="muplugins", to="netbox_wordpress.wordpresssite")),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "verbose_name": "WordPress Must-Use Plugin",
                "ordering": ["site", "name"],
                "constraints": [models.UniqueConstraint(fields=("site", "name"), name="netbox_wordpress_wordpressmuplugin_unique_site_name")],
            },
        ),
    ]
