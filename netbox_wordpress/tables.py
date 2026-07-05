# SPDX-License-Identifier: AGPL-3.0-or-later
import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import (
    WordPressConstant, WordPressContentDirectory, WordPressPlugin, WordPressSite, WordPressTheme,
)


class WordPressSiteTable(NetBoxTable):
    name = tables.Column(linkify=True)
    device = tables.Column(linkify=True)
    virtual_machine = tables.Column(linkify=True)
    is_multisite = columns.BooleanColumn()
    fpm_profile = columns.ChoiceFieldColumn()
    prod_hardening = columns.BooleanColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_wordpress:wordpresssite_list")

    class Meta(NetBoxTable.Meta):
        model = WordPressSite
        fields = (
            "pk", "id", "name", "device", "virtual_machine", "service_instance", "site_url",
            "wp_version", "table_prefix", "is_multisite", "database", "db_user", "fpm_profile",
            "wp_memory_limit", "prod_hardening", "salt_ref", "tags", "created", "last_updated",
        )
        default_columns = ("name", "site_url", "wp_version", "is_multisite", "fpm_profile")


class WordPressConstantTable(NetBoxTable):
    site = tables.Column(linkify=True)
    name = tables.Column(linkify=True)
    value_type = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_wordpress:wordpressconstant_list")

    class Meta(NetBoxTable.Meta):
        model = WordPressConstant
        fields = ("pk", "id", "site", "name", "value", "value_type", "tags", "created", "last_updated")
        default_columns = ("site", "name", "value", "value_type")


class WordPressPluginTable(NetBoxTable):
    site = tables.Column(linkify=True)
    slug = tables.Column(linkify=True)
    is_active = columns.BooleanColumn()
    source = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_wordpress:wordpressplugin_list")

    class Meta(NetBoxTable.Meta):
        model = WordPressPlugin
        fields = ("pk", "id", "site", "slug", "version", "is_active", "source", "source_url", "tags", "created", "last_updated")
        default_columns = ("site", "slug", "version", "is_active", "source")


class WordPressThemeTable(NetBoxTable):
    site = tables.Column(linkify=True)
    slug = tables.Column(linkify=True)
    is_active = columns.BooleanColumn()
    source = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_wordpress:wordpresstheme_list")

    class Meta(NetBoxTable.Meta):
        model = WordPressTheme
        fields = ("pk", "id", "site", "slug", "version", "is_active", "source", "source_url", "tags", "created", "last_updated")
        default_columns = ("site", "slug", "version", "is_active", "source")


class WordPressContentDirectoryTable(NetBoxTable):
    site = tables.Column(linkify=True)
    content_dir = tables.Column(linkify=True)
    relocation_state = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_wordpress:wordpresscontentdirectory_list")

    class Meta(NetBoxTable.Meta):
        model = WordPressContentDirectory
        fields = ("pk", "id", "site", "content_dir", "uploads_dir", "target_content_dir", "content_url", "relocation_state", "tags", "created", "last_updated")
        default_columns = ("site", "content_dir", "target_content_dir", "relocation_state")
