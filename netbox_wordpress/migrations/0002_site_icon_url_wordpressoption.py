# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_wordpress --check --dry-run
import django.db.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("extras", "0001_initial"),
        ("netbox_wordpress", "0001_initial"),
    ]
    operations = [
        migrations.AddField(
            model_name="wordpresssite",
            name="site_icon_url",
            field=models.URLField(blank=True),
        ),
        migrations.CreateModel(
            name="WordPressOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, blank=True, null=True)),
                ("custom_field_data", models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
                ("name", models.CharField(max_length=191)),
                ("key_path", models.CharField(blank=True, max_length=255)),
                ("value", models.TextField()),
                ("value_format", models.CharField(default="string", max_length=8)),
                ("site", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="options", to="netbox_wordpress.wordpresssite")),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "verbose_name": "WordPress Option",
                "ordering": ["site", "name", "key_path"],
                "constraints": [models.UniqueConstraint(fields=("site", "name", "key_path"), name="netbox_wordpress_wordpressoption_unique_site_name_key")],
            },
        ),
    ]
