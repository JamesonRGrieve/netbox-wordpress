# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored initial migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_wordpress --check --dry-run   (on a dev/ephemeral NetBox)
# Re-confirm against the pinned NetBox 4.6: the cross-plugin FK targets
# netbox_services.ServiceInstance and netbox_database.Database / netbox_database.DatabaseUser
# (those apps' 0001_initial must have created the tables — hence the dependencies below).
import django.db.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models

_BASE = [
    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
    ("created", models.DateTimeField(auto_now_add=True, blank=True, null=True)),
    ("last_updated", models.DateTimeField(auto_now=True, blank=True, null=True)),
    ("custom_field_data", models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
]
_TAGS = ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"))


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("dcim", "0001_initial"),
        ("virtualization", "0001_virtualization"),
        ("extras", "0001_initial"),
        ("netbox_services", "0001_initial"),
        ("netbox_database", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="WordPressSite",
            fields=[
                *_BASE,
                ("name", models.CharField(max_length=128, unique=True)),
                ("site_url", models.URLField(blank=True)),
                ("wp_version", models.CharField(blank=True, max_length=32)),
                ("table_prefix", models.CharField(default="wp_", max_length=64)),
                ("is_multisite", models.BooleanField(default=False)),
                ("fpm_profile", models.CharField(blank=True, max_length=8)),
                ("wp_memory_limit", models.CharField(blank=True, max_length=16)),
                ("prod_hardening", models.BooleanField(default=False)),
                ("salt_ref", models.CharField(blank=True, max_length=255)),
                ("device", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="wordpress_sites", to="dcim.device")),
                ("virtual_machine", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="wordpress_sites", to="virtualization.virtualmachine")),
                ("service_instance", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="wordpress_sites", to="netbox_services.serviceinstance")),
                ("database", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="wordpress_sites", to="netbox_database.database")),
                ("db_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="wordpress_sites", to="netbox_database.databaseuser")),
                _TAGS,
            ],
            options={"verbose_name": "WordPress Site", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="WordPressConstant",
            fields=[
                *_BASE,
                ("name", models.CharField(max_length=128)),
                ("value", models.CharField(max_length=255)),
                ("value_type", models.CharField(default="string", max_length=8)),
                ("site", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="constants", to="netbox_wordpress.wordpresssite")),
                _TAGS,
            ],
            options={
                "verbose_name": "WordPress Constant",
                "ordering": ["site", "name"],
                "constraints": [models.UniqueConstraint(fields=("site", "name"), name="netbox_wordpress_wordpressconstant_unique_site_name")],
            },
        ),
        migrations.CreateModel(
            name="WordPressPlugin",
            fields=[
                *_BASE,
                ("slug", models.CharField(max_length=128)),
                ("version", models.CharField(blank=True, max_length=32)),
                ("is_active", models.BooleanField(default=True)),
                ("source", models.CharField(default="wporg", max_length=8)),
                ("source_url", models.URLField(blank=True)),
                ("site", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="plugins", to="netbox_wordpress.wordpresssite")),
                _TAGS,
            ],
            options={
                "verbose_name": "WordPress Plugin",
                "ordering": ["site", "slug"],
                "constraints": [models.UniqueConstraint(fields=("site", "slug"), name="netbox_wordpress_wordpressplugin_unique_site_slug")],
            },
        ),
        migrations.CreateModel(
            name="WordPressTheme",
            fields=[
                *_BASE,
                ("slug", models.CharField(max_length=128)),
                ("version", models.CharField(blank=True, max_length=32)),
                ("is_active", models.BooleanField(default=False)),
                ("source", models.CharField(default="wporg", max_length=8)),
                ("source_url", models.URLField(blank=True)),
                ("site", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="themes", to="netbox_wordpress.wordpresssite")),
                _TAGS,
            ],
            options={
                "verbose_name": "WordPress Theme",
                "ordering": ["site", "slug"],
                "constraints": [models.UniqueConstraint(fields=("site", "slug"), name="netbox_wordpress_wordpresstheme_unique_site_slug")],
            },
        ),
        migrations.CreateModel(
            name="WordPressContentDirectory",
            fields=[
                *_BASE,
                ("content_dir", models.CharField(default="/var/www/html/wp-content", max_length=255)),
                ("uploads_dir", models.CharField(blank=True, max_length=255)),
                ("target_content_dir", models.CharField(blank=True, max_length=255)),
                ("content_url", models.CharField(blank=True, max_length=255)),
                ("relocation_state", models.CharField(default="in_place", max_length=16)),
                ("site", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="content_directory", to="netbox_wordpress.wordpresssite")),
                _TAGS,
            ],
            options={"verbose_name": "WordPress Content Directory", "ordering": ["site"]},
        ),
    ]
