# SPDX-License-Identifier: AGPL-3.0-or-later
"""REST API CRUD tests against a real DB + real API client (no mocks).

Composes the explicit CRUD mixins (not the GraphQL-inclusive APIViewTestCase) since the plugin
ships no GraphQL type yet. WordPressSite host-binds to a fresh device per row; WordPressContentDirectory
is 1:1 to a site, so each create_data row targets a fresh site."""
from utilities.testing import APIViewTestCases, create_test_device

from netbox_wordpress.models import (
    WordPressConstant, WordPressContentDirectory, WordPressPlugin, WordPressSite, WordPressTheme,
)
from netbox_wordpress.tests.utils import create_wp_site


class _CRUD(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    pass


class WordPressSiteAPITest(_CRUD):
    model = WordPressSite
    brief_fields = ["display", "id", "name", "site_url", "url"]
    bulk_update_data = {"wp_version": "6.5.2"}

    @classmethod
    def setUpTestData(cls):
        WordPressSite.objects.bulk_create([
            WordPressSite(name=f"exist-{i}", device=create_test_device(f"h-{i}")) for i in range(3)
        ])
        new = [create_test_device(f"hn-{i}") for i in range(3)]
        cls.create_data = [
            {"name": "shop", "device": new[0].pk, "site_url": "https://shop.example", "wp_version": "6.5", "fpm_profile": "high"},
            {"name": "brochure", "device": new[1].pk, "table_prefix": "bx_", "is_multisite": True},
            {"name": "hardened", "device": new[2].pk, "prod_hardening": True, "salt_ref": "wp/salts/hardened"},
        ]


class WordPressConstantAPITest(_CRUD):
    model = WordPressConstant
    brief_fields = ["display", "id", "name", "url", "value"]
    bulk_update_data = {"value_type": "bool"}

    @classmethod
    def setUpTestData(cls):
        site = create_wp_site("const-api")
        WordPressConstant.objects.bulk_create([
            WordPressConstant(site=site, name="WP_DEBUG", value="false", value_type="bool"),
            WordPressConstant(site=site, name="WP_MEMORY_LIMIT", value="256M"),
            WordPressConstant(site=site, name="WP_POST_REVISIONS", value="5", value_type="int"),
        ])
        cls.create_data = [
            {"site": site.pk, "name": "DISABLE_WP_CRON", "value": "true", "value_type": "bool"},
            {"site": site.pk, "name": "WP_AUTO_UPDATE_CORE", "value": "minor", "value_type": "string"},
            {"site": site.pk, "name": "EMPTY_TRASH_DAYS", "value": "7", "value_type": "int"},
        ]


class WordPressPluginAPITest(_CRUD):
    model = WordPressPlugin
    brief_fields = ["display", "id", "slug", "url", "version"]
    bulk_update_data = {"is_active": False}

    @classmethod
    def setUpTestData(cls):
        site = create_wp_site("plugin-api")
        WordPressPlugin.objects.bulk_create([
            WordPressPlugin(site=site, slug="woocommerce"),
            WordPressPlugin(site=site, slug="cache-enabler", version="1.8.0"),
            WordPressPlugin(site=site, slug="redis-cache", source="zip", source_url="https://example.com/redis.zip"),
        ])
        cls.create_data = [
            {"site": site.pk, "slug": "jetpack", "version": "13.0", "is_active": True, "source": "wporg"},
            {"site": site.pk, "slug": "custom", "source": "url", "source_url": "https://example.com/custom.zip"},
            {"site": site.pk, "slug": "yoast", "is_active": False},
        ]


class WordPressThemeAPITest(_CRUD):
    model = WordPressTheme
    brief_fields = ["display", "id", "slug", "url", "version"]
    bulk_update_data = {"is_active": True}

    @classmethod
    def setUpTestData(cls):
        site = create_wp_site("theme-api")
        WordPressTheme.objects.bulk_create([
            WordPressTheme(site=site, slug="twentytwentyfour", is_active=True),
            WordPressTheme(site=site, slug="astra"),
            WordPressTheme(site=site, slug="custom", source="zip", source_url="https://example.com/theme.zip"),
        ])
        cls.create_data = [
            {"site": site.pk, "slug": "generatepress", "version": "3.4", "source": "wporg"},
            {"site": site.pk, "slug": "kadence", "is_active": False},
            {"site": site.pk, "slug": "hello-elementor", "source": "url", "source_url": "https://example.com/h.zip"},
        ]


class WordPressContentDirectoryAPITest(_CRUD):
    model = WordPressContentDirectory
    brief_fields = ["content_dir", "display", "id", "site", "url"]
    bulk_update_data = {"relocation_state": "relocated"}

    @classmethod
    def setUpTestData(cls):
        existing = [create_wp_site(f"cd-exist-{i}") for i in range(3)]
        WordPressContentDirectory.objects.bulk_create([
            WordPressContentDirectory(site=s, content_dir=f"/var/www/site{i}/wp-content") for i, s in enumerate(existing)
        ])
        new = [create_wp_site(f"cd-new-{i}") for i in range(3)]
        cls.create_data = [
            {"site": new[0].pk, "content_dir": "/var/www/html/wp-content"},
            {"site": new[1].pk, "content_dir": "/var/www/html/wp-content", "target_content_dir": "/srv/wp-content", "relocation_state": "relocating"},
            {"site": new[2].pk, "content_dir": "/opt/wp/content", "uploads_dir": "/opt/wp/uploads", "content_url": "https://x.example/wp-content"},
        ]
