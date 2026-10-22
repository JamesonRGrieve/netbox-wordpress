# SPDX-License-Identifier: AGPL-3.0-or-later
import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import (
    WordPressConstant, WordPressContentDirectory, WordPressMuPlugin, WordPressOption, WordPressPlugin,
    WordPressSite, WordPressTheme,
)


class WordPressSiteTable(NetBoxTable):
    name = tables.Column(linkify=True)
    device = tables.Column(linkify=True)
    virtual_machine = tables.Column(linkify=True)
    object_cache_instance = tables.Column(linkify=True)
    is_multisite = columns.BooleanColumn()
    fpm_profile = columns.ChoiceFieldColumn()
    prod_hardening = columns.BooleanColumn()
    safe_opt = columns.BooleanColumn()
    enable_hsts = columns.BooleanColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_wordpress:wordpresssite_list")

    class Meta(NetBoxTable.Meta):
        model = WordPressSite
        fields = (
            "pk", "id", "name", "device", "virtual_machine", "service_instance",
            "object_cache_instance", "site_url", "wp_version", "table_prefix", "is_multisite",
            "install_path", "database", "db_user", "fpm_profile", "wp_memory_limit", "prod_hardening",
            "safe_opt", "login_slug", "trusted_proxies", "enable_hsts", "salt_ref", "site_icon_url", "tags",
            "created", "last_updated",
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


class WordPressOptionTable(NetBoxTable):
    site = tables.Column(linkify=True)
    name = tables.Column(linkify=True)
    value_format = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_wordpress:wordpressoption_list")

    class Meta(NetBoxTable.Meta):
        model = WordPressOption
        fields = ("pk", "id", "site", "name", "key_path", "value", "value_format", "tags", "created", "last_updated")
        default_columns = ("site", "name", "key_path", "value", "value_format")


class WordPressPluginTable(NetBoxTable):
    site = tables.Column(linkify=True)
    slug = tables.Column(linkify=True)
    state = columns.ChoiceFieldColumn()
    source = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_wordpress:wordpressplugin_list")

    class Meta(NetBoxTable.Meta):
        model = WordPressPlugin
        fields = ("pk", "id", "site", "slug", "version", "state", "source", "source_url", "tags", "created", "last_updated")
        default_columns = ("site", "slug", "version", "state", "source")


class WordPressMuPluginTable(NetBoxTable):
    site = tables.Column(linkify=True)
    name = tables.Column(linkify=True)
    tags = columns.TagColumn(url_name="plugins:netbox_wordpress:wordpressmuplugin_list")

    class Meta(NetBoxTable.Meta):
        model = WordPressMuPlugin
        fields = (
            "pk", "id", "site", "name", "repository", "commit", "source_path", "sha256", "description", "tags",
            "created", "last_updated",
        )
        default_columns = ("site", "name", "repository", "commit", "source_path")


class WordPressThemeTable(NetBoxTable):
    site = tables.Column(linkify=True)
    slug = tables.Column(linkify=True)
    state = columns.ChoiceFieldColumn()
    source = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_wordpress:wordpresstheme_list")

    class Meta(NetBoxTable.Meta):
        model = WordPressTheme
        fields = ("pk", "id", "site", "slug", "version", "state", "source", "source_url", "tags", "created", "last_updated")
        default_columns = ("site", "slug", "version", "state", "source")


class WordPressContentDirectoryTable(NetBoxTable):
    site = tables.Column(linkify=True)
    content_dir = tables.Column(linkify=True)
    relocation_state = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_wordpress:wordpresscontentdirectory_list")

    class Meta(NetBoxTable.Meta):
        model = WordPressContentDirectory
        fields = ("pk", "id", "site", "content_dir", "uploads_dir", "target_content_dir", "content_url", "relocation_state", "tags", "created", "last_updated")
        default_columns = ("site", "content_dir", "target_content_dir", "relocation_state")
