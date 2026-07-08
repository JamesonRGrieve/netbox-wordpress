# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from ..models import (
    WordPressConstant, WordPressContentDirectory, WordPressPlugin, WordPressSite, WordPressTheme,
)


class WordPressSiteSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_wordpress-api:wordpresssite-detail")

    class Meta:
        model = WordPressSite
        fields = [
            "id", "url", "display", "name", "device", "virtual_machine", "service_instance",
            "object_cache_instance", "site_url", "wp_version", "table_prefix", "is_multisite",
            "install_path", "database", "db_user", "fpm_profile", "wp_memory_limit", "prod_hardening",
            "safe_opt", "login_slug", "trusted_proxies", "enable_hsts", "salt_ref",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "name", "site_url"]


class WordPressConstantSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_wordpress-api:wordpressconstant-detail")
    site = WordPressSiteSerializer(nested=True)

    class Meta:
        model = WordPressConstant
        fields = [
            "id", "url", "display", "site", "name", "value", "value_type",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "name", "value"]


class WordPressPluginSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_wordpress-api:wordpressplugin-detail")
    site = WordPressSiteSerializer(nested=True)

    class Meta:
        model = WordPressPlugin
        fields = [
            "id", "url", "display", "site", "slug", "version", "state", "source", "source_url",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "slug", "version"]


class WordPressThemeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_wordpress-api:wordpresstheme-detail")
    site = WordPressSiteSerializer(nested=True)

    class Meta:
        model = WordPressTheme
        fields = [
            "id", "url", "display", "site", "slug", "version", "state", "source", "source_url",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "slug", "version"]


class WordPressContentDirectorySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_wordpress-api:wordpresscontentdirectory-detail")
    site = WordPressSiteSerializer(nested=True)

    class Meta:
        model = WordPressContentDirectory
        fields = [
            "id", "url", "display", "site", "content_dir", "uploads_dir", "target_content_dir",
            "content_url", "relocation_state",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "site", "content_dir"]
