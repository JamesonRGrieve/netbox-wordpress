# SPDX-License-Identifier: AGPL-3.0-or-later
"""FilterSet tests against a real DB (no mocks)."""
from django.test import TestCase
from utilities.testing import create_test_device

from netbox_wordpress.choices import (
    FPMProfileChoices, PluginSourceChoices, PluginStateChoices, RelocationStateChoices,
    WPConstantTypeChoices, WPOptionFormatChoices,
)
from netbox_wordpress.filtersets import (
    WordPressConstantFilterSet, WordPressContentDirectoryFilterSet, WordPressMuPluginFilterSet,
    WordPressOptionFilterSet, WordPressPluginFilterSet, WordPressSiteFilterSet, WordPressThemeFilterSet,
)
from netbox_wordpress.models import (
    WordPressConstant, WordPressContentDirectory, WordPressMuPlugin, WordPressOption, WordPressPlugin,
    WordPressSite, WordPressTheme,
)
from netbox_wordpress.tests.utils import create_wp_site


class WordPressSiteFilterSetTest(TestCase):
    queryset = WordPressSite.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.d1 = create_test_device("dev1")
        cls.d2 = create_test_device("dev2")
        WordPressSite.objects.create(name="alpha", device=cls.d1, fpm_profile=FPMProfileChoices.LOW, is_multisite=True, safe_opt=True, enable_hsts=True)
        WordPressSite.objects.create(name="bravo", device=cls.d2, fpm_profile=FPMProfileChoices.HIGH)

    def test_device_id_scopes(self):
        self.assertEqual(WordPressSiteFilterSet({"device_id": [self.d1.pk]}, self.queryset).qs.count(), 1)

    def test_fpm_profile(self):
        self.assertEqual(WordPressSiteFilterSet({"fpm_profile": [FPMProfileChoices.HIGH]}, self.queryset).qs.count(), 1)

    def test_is_multisite(self):
        self.assertEqual(WordPressSiteFilterSet({"is_multisite": True}, self.queryset).qs.count(), 1)

    def test_safe_opt(self):
        self.assertEqual(WordPressSiteFilterSet({"safe_opt": True}, self.queryset).qs.count(), 1)

    def test_enable_hsts(self):
        self.assertEqual(WordPressSiteFilterSet({"enable_hsts": True}, self.queryset).qs.count(), 1)

    def test_site_icon_url(self):
        WordPressSite.objects.filter(name="alpha").update(site_icon_url="https://cdn.example/a.png")
        self.assertEqual(WordPressSiteFilterSet({"site_icon_url": ["https://cdn.example/a.png"]}, self.queryset).qs.count(), 1)

    def test_search(self):
        self.assertEqual(WordPressSiteFilterSet({"q": "alpha"}, self.queryset).qs.count(), 1)


class WordPressConstantFilterSetTest(TestCase):
    queryset = WordPressConstant.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.s1 = create_wp_site("s1")
        cls.s2 = create_wp_site("s2")
        WordPressConstant.objects.bulk_create([
            WordPressConstant(site=cls.s1, name="WP_DEBUG", value="false", value_type=WPConstantTypeChoices.BOOL),
            WordPressConstant(site=cls.s1, name="WP_MEMORY_LIMIT", value="256M", value_type=WPConstantTypeChoices.STRING),
            WordPressConstant(site=cls.s2, name="WP_DEBUG", value="true", value_type=WPConstantTypeChoices.BOOL),
        ])

    def test_site_id_scopes(self):
        self.assertEqual(WordPressConstantFilterSet({"site_id": [self.s1.pk]}, self.queryset).qs.count(), 2)

    def test_value_type(self):
        self.assertEqual(WordPressConstantFilterSet({"value_type": [WPConstantTypeChoices.BOOL]}, self.queryset).qs.count(), 2)

    def test_search(self):
        self.assertEqual(WordPressConstantFilterSet({"q": "WP_MEMORY_LIMIT"}, self.queryset).qs.count(), 1)


class WordPressOptionFilterSetTest(TestCase):
    queryset = WordPressOption.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.s1 = create_wp_site("o1")
        cls.s2 = create_wp_site("o2")
        WordPressOption.objects.bulk_create([
            WordPressOption(site=cls.s1, name="wpseo", key_path="enable_xml_sitemap", value="true", value_format=WPOptionFormatChoices.JSON),
            WordPressOption(site=cls.s1, name="blog_public", value="1"),
            WordPressOption(site=cls.s2, name="wpseo", key_path="enable_xml_sitemap", value="false", value_format=WPOptionFormatChoices.JSON),
        ])

    def test_site_id_scopes(self):
        self.assertEqual(WordPressOptionFilterSet({"site_id": [self.s1.pk]}, self.queryset).qs.count(), 2)

    def test_site_name_scopes(self):
        self.assertEqual(WordPressOptionFilterSet({"site": ["o2"]}, self.queryset).qs.count(), 1)

    def test_name_and_key_path(self):
        self.assertEqual(WordPressOptionFilterSet({"name": ["wpseo"], "key_path": ["enable_xml_sitemap"]}, self.queryset).qs.count(), 2)

    def test_value_format(self):
        self.assertEqual(WordPressOptionFilterSet({"value_format": [WPOptionFormatChoices.STRING]}, self.queryset).qs.count(), 1)

    def test_search(self):
        self.assertEqual(WordPressOptionFilterSet({"q": "xml_sitemap"}, self.queryset).qs.count(), 2)


class WordPressPluginFilterSetTest(TestCase):
    queryset = WordPressPlugin.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.s1 = create_wp_site("p1")
        cls.s2 = create_wp_site("p2")
        WordPressPlugin.objects.bulk_create([
            WordPressPlugin(site=cls.s1, slug="woocommerce", source=PluginSourceChoices.WPORG, state=PluginStateChoices.ACTIVE),
            WordPressPlugin(site=cls.s1, slug="w3-total-cache", source=PluginSourceChoices.ZIP, state=PluginStateChoices.ABSENT),
            WordPressPlugin(site=cls.s2, slug="jetpack", source=PluginSourceChoices.WPORG, state=PluginStateChoices.ACTIVE),
            WordPressPlugin(site=cls.s2, slug="wp-woo-scan-in", source=PluginSourceChoices.FORGEJO,
                            state=PluginStateChoices.PRESENT_INACTIVE,
                            repository="ObsessedMediaGroup/wp-woo-scan-in", commit="1b6587a9f29c99e1c1d7850f4f20b9e3399407bf"),
        ])

    def test_site_id_scopes(self):
        self.assertEqual(WordPressPluginFilterSet({"site_id": [self.s1.pk]}, self.queryset).qs.count(), 2)

    def test_forgejo_source_repository_and_commit(self):
        fs = WordPressPluginFilterSet
        self.assertEqual(fs({"source": [PluginSourceChoices.FORGEJO]}, self.queryset).qs.get().slug, "wp-woo-scan-in")
        self.assertEqual(fs({"repository": ["ObsessedMediaGroup/wp-woo-scan-in"]}, self.queryset).qs.count(), 1)
        self.assertEqual(fs({"commit": ["1b6587a9f29c99e1c1d7850f4f20b9e3399407bf"]}, self.queryset).qs.count(), 1)
        self.assertEqual(fs({"q": "ObsessedMediaGroup"}, self.queryset).qs.count(), 1)

    def test_source(self):
        self.assertEqual(WordPressPluginFilterSet({"source": [PluginSourceChoices.ZIP]}, self.queryset).qs.count(), 1)

    def test_state_active(self):
        self.assertEqual(WordPressPluginFilterSet({"state": [PluginStateChoices.ACTIVE]}, self.queryset).qs.count(), 2)

    def test_state_absent(self):
        self.assertEqual(WordPressPluginFilterSet({"state": [PluginStateChoices.ABSENT]}, self.queryset).qs.count(), 1)

    def test_search(self):
        self.assertEqual(WordPressPluginFilterSet({"q": "woocommerce"}, self.queryset).qs.count(), 1)


class WordPressMuPluginFilterSetTest(TestCase):
    queryset = WordPressMuPlugin.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.s1 = create_wp_site("mu1")
        cls.s2 = create_wp_site("mu2")
        WordPressMuPlugin.objects.bulk_create([
            WordPressMuPlugin(site=cls.s1, name="square-guard.php", repository="Org1/guards", commit="1" * 40, source_path="files/mu1/square-guard.php", sha256="a" * 64, description="Square catalogue guard"),
            WordPressMuPlugin(site=cls.s1, name="session.php", repository="Org1/guards", commit="1" * 40, source_path="files/mu1/session.php", sha256="b" * 64),
            WordPressMuPlugin(site=cls.s2, name="square-guard.php", repository="Org2/sync", commit="2" * 40, source_path="files/mu2/square-guard.php", sha256="c" * 64),
        ])

    def test_site_id_scopes(self):
        self.assertEqual(WordPressMuPluginFilterSet({"site_id": [self.s1.pk]}, self.queryset).qs.count(), 2)

    def test_site_name_scopes(self):
        self.assertEqual(WordPressMuPluginFilterSet({"site": ["mu2"]}, self.queryset).qs.count(), 1)

    def test_name(self):
        self.assertEqual(WordPressMuPluginFilterSet({"name": ["square-guard.php"]}, self.queryset).qs.count(), 2)

    def test_repository_and_commit(self):
        self.assertEqual(WordPressMuPluginFilterSet({"repository": ["Org1/guards"]}, self.queryset).qs.count(), 2)
        self.assertEqual(WordPressMuPluginFilterSet({"commit": ["2" * 40]}, self.queryset).qs.count(), 1)

    def test_search_name_path_description(self):
        self.assertEqual(WordPressMuPluginFilterSet({"q": "Org2/"}, self.queryset).qs.count(), 1)
        self.assertEqual(WordPressMuPluginFilterSet({"q": "session"}, self.queryset).qs.count(), 1)
        self.assertEqual(WordPressMuPluginFilterSet({"q": "files/mu2"}, self.queryset).qs.count(), 1)
        self.assertEqual(WordPressMuPluginFilterSet({"q": "catalogue"}, self.queryset).qs.count(), 1)


class WordPressThemeFilterSetTest(TestCase):
    queryset = WordPressTheme.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.s1 = create_wp_site("t1")
        cls.s2 = create_wp_site("t2")
        WordPressTheme.objects.bulk_create([
            WordPressTheme(site=cls.s1, slug="twentytwentyfour", state=PluginStateChoices.ACTIVE),
            WordPressTheme(site=cls.s1, slug="astra", state=PluginStateChoices.PRESENT_INACTIVE),
            WordPressTheme(site=cls.s2, slug="kadence", source=PluginSourceChoices.ZIP),
        ])

    def test_site_id_scopes(self):
        self.assertEqual(WordPressThemeFilterSet({"site_id": [self.s1.pk]}, self.queryset).qs.count(), 2)

    def test_source(self):
        self.assertEqual(WordPressThemeFilterSet({"source": [PluginSourceChoices.ZIP]}, self.queryset).qs.count(), 1)

    def test_search(self):
        self.assertEqual(WordPressThemeFilterSet({"q": "astra"}, self.queryset).qs.count(), 1)


class WordPressContentDirectoryFilterSetTest(TestCase):
    queryset = WordPressContentDirectory.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.s1 = create_wp_site("cd1")
        cls.s2 = create_wp_site("cd2")
        WordPressContentDirectory.objects.create(site=cls.s1, content_dir="/var/www/a/wp-content", relocation_state=RelocationStateChoices.IN_PLACE)
        WordPressContentDirectory.objects.create(site=cls.s2, content_dir="/var/www/b/wp-content", target_content_dir="/srv/b", relocation_state=RelocationStateChoices.RELOCATING)

    def test_site_id_scopes(self):
        self.assertEqual(WordPressContentDirectoryFilterSet({"site_id": [self.s1.pk]}, self.queryset).qs.count(), 1)

    def test_relocation_state(self):
        self.assertEqual(WordPressContentDirectoryFilterSet({"relocation_state": [RelocationStateChoices.RELOCATING]}, self.queryset).qs.count(), 1)

    def test_search(self):
        self.assertEqual(WordPressContentDirectoryFilterSet({"q": "/srv/b"}, self.queryset).qs.count(), 1)
