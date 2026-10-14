# SPDX-License-Identifier: AGPL-3.0-or-later
"""REST API CRUD tests against a real DB + real API client (no mocks).

Composes the explicit CRUD mixins (not the GraphQL-inclusive APIViewTestCase) since the plugin
ships no GraphQL type yet. WordPressSite host-binds to a fresh device per row; WordPressContentDirectory
is 1:1 to a site, so each create_data row targets a fresh site."""
import unittest

from utilities.testing import APIViewTestCases, create_test_device

from netbox_wordpress.models import (
    WordPressConstant, WordPressContentDirectory, WordPressOption, WordPressPlugin, WordPressSite,
    WordPressTheme,
)
from netbox_wordpress.tests.utils import create_wp_site


class _CRUD(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    # Plugin API views register under the `plugins-api:<app_label>-api` namespace;
    # without this override the test base reverses `<app_label>-api:…` (no
    # `plugins-api` prefix) → NoReverseMatch. See utilities/testing/api.py.
    view_namespace = "plugins-api:netbox_wordpress"

    @classmethod
    def setUpClass(cls):
        # _CRUD is an abstract base (no `model`); Django's test loader still
        # collects it. Skip it so only the concrete subclasses run.
        if cls is _CRUD:
            raise unittest.SkipTest("abstract API test base")
        super().setUpClass()


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
            {"name": "shop", "device": new[0].pk, "site_url": "https://shop.example", "wp_version": "6.5", "fpm_profile": "high", "safe_opt": True},
            {"name": "brochure", "device": new[1].pk, "table_prefix": "bx_", "is_multisite": True, "install_path": "/var/www/html"},
            {"name": "hardened", "device": new[2].pk, "prod_hardening": True, "salt_ref": "wp/salts/hardened", "login_slug": "KzfYwpdC", "trusted_proxies": "10.0.0.1", "enable_hsts": True, "site_icon_url": "https://cdn.example/hardened-512.png"},
        ]


class WordPressConstantAPITest(_CRUD):
    model = WordPressConstant
    brief_fields = ["display", "id", "name", "url", "value"]
    # "raw" — a value_type none of the seed constants already has, so every row
    # actually changes (the bulk-update test asserts len(changes) == len(data)).
    bulk_update_data = {"value_type": "raw"}

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


class WordPressOptionAPITest(_CRUD):
    model = WordPressOption
    brief_fields = ["display", "id", "key_path", "name", "url", "value"]
    # "json" with a JSON-valid value — every seed row is "string", so each row actually changes.
    bulk_update_data = {"value_format": "json", "value": "true"}

    @classmethod
    def setUpTestData(cls):
        site = create_wp_site("option-api")
        WordPressOption.objects.bulk_create([
            WordPressOption(site=site, name="blog_public", value="1"),
            WordPressOption(site=site, name="blogdescription", value="Just another site"),
            WordPressOption(site=site, name="wpseo", key_path="enable_xml_sitemap", value="1"),
        ])
        cls.create_data = [
            {"site": site.pk, "name": "wpseo", "key_path": "disableadvanced_meta", "value": "false", "value_format": "json"},
            {"site": site.pk, "name": "permalink_structure", "value": "/%postname%/"},
            {"site": site.pk, "name": "wpseo_titles", "key_path": "noindex-page", "value": "false", "value_format": "json"},
        ]

    def test_json_value_must_parse(self):
        self.add_permissions("netbox_wordpress.add_wordpressoption")
        site = WordPressSite.objects.get(name="option-api")
        resp = self.client.post(
            self._get_list_url(),
            {"site": site.pk, "name": "bad", "value": "{oops", "value_format": "json"},
            format="json", **self.header,
        )
        self.assertHttpStatus(resp, 400)


class WordPressPluginAPITest(_CRUD):
    model = WordPressPlugin
    brief_fields = ["display", "id", "slug", "url", "version"]
    bulk_update_data = {"state": "present_inactive"}

    @classmethod
    def setUpTestData(cls):
        site = create_wp_site("plugin-api")
        WordPressPlugin.objects.bulk_create([
            WordPressPlugin(site=site, slug="woocommerce"),
            WordPressPlugin(site=site, slug="cache-enabler", version="1.8.0"),
            WordPressPlugin(site=site, slug="redis-cache", source="zip", source_url="https://example.com/redis.zip"),
        ])
        cls.create_data = [
            {"site": site.pk, "slug": "jetpack", "version": "13.0", "state": "active", "source": "wporg"},
            {"site": site.pk, "slug": "custom", "source": "url", "source_url": "https://example.com/custom.zip"},
            {"site": site.pk, "slug": "w3-total-cache", "state": "absent"},
        ]


class WordPressThemeAPITest(_CRUD):
    model = WordPressTheme
    brief_fields = ["display", "id", "slug", "url", "version"]
    # "absent" — a state none of the seed themes already has, so every row changes.
    bulk_update_data = {"state": "absent"}

    @classmethod
    def setUpTestData(cls):
        site = create_wp_site("theme-api")
        WordPressTheme.objects.bulk_create([
            WordPressTheme(site=site, slug="twentytwentyfour", state="active"),
            WordPressTheme(site=site, slug="astra"),
            WordPressTheme(site=site, slug="custom", source="zip", source_url="https://example.com/theme.zip"),
        ])
        cls.create_data = [
            {"site": site.pk, "slug": "generatepress", "version": "3.4", "source": "wporg"},
            {"site": site.pk, "slug": "kadence", "state": "present_inactive"},
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
