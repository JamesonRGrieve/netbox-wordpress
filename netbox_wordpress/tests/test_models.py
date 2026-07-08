# SPDX-License-Identifier: AGPL-3.0-or-later
"""Model tests against a real DB (no mocks): the exactly-one-host clean() rule, uniqueness
constraints, defaults, str/url, and cascade behaviour."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from django.test import TestCase
from utilities.testing import create_test_device

from netbox_wordpress.choices import (
    PluginSourceChoices, PluginStateChoices, RelocationStateChoices, WPConstantTypeChoices,
)
from netbox_wordpress.models import (
    WordPressConstant, WordPressContentDirectory, WordPressPlugin, WordPressSite, WordPressTheme,
)
from netbox_wordpress.tests.utils import create_test_vm, create_wp_site


class WordPressSiteModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device("dev1")

    def test_create_defaults_str_url(self):
        s = WordPressSite.objects.create(name="blog", device=self.device)
        self.assertEqual(s.table_prefix, "wp_")
        self.assertFalse(s.is_multisite)
        self.assertFalse(s.prod_hardening)
        self.assertFalse(s.safe_opt)
        self.assertFalse(s.enable_hsts)
        self.assertEqual(s.login_slug, "")
        self.assertEqual(s.install_path, "")
        self.assertEqual(s.trusted_proxies, "")
        self.assertIsNone(s.object_cache_instance)
        self.assertEqual(str(s), "blog")
        self.assertIn("/plugins/wordpress/sites/", s.get_absolute_url())

    def test_security_and_tuning_fields_persist(self):
        s = WordPressSite.objects.create(
            name="hardened", device=create_test_device("d-hard"), login_slug="KzfYwpdC",
            install_path="/var/www/html", safe_opt=True, prod_hardening=True, enable_hsts=True,
            trusted_proxies="192.168.255.1,10.0.0.0/8",
        )
        s.refresh_from_db()
        self.assertEqual(s.login_slug, "KzfYwpdC")
        self.assertEqual(s.install_path, "/var/www/html")
        self.assertTrue(s.safe_opt)
        self.assertTrue(s.enable_hsts)
        self.assertEqual(s.trusted_proxies, "192.168.255.1,10.0.0.0/8")

    def test_name_unique(self):
        WordPressSite.objects.create(name="dup", device=create_test_device("d-a"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            WordPressSite.objects.create(name="dup", device=create_test_device("d-b"))

    def test_clean_device_only_ok(self):
        WordPressSite(name="ok-dev", device=self.device).clean()  # no raise

    def test_clean_vm_only_ok(self):
        WordPressSite(name="ok-vm", virtual_machine=create_test_vm("vm-ok")).clean()  # no raise

    def test_clean_neither_host_raises(self):
        with self.assertRaises(ValidationError):
            WordPressSite(name="no-host").clean()

    def test_clean_both_hosts_raises(self):
        with self.assertRaises(ValidationError):
            WordPressSite(name="two-host", device=self.device, virtual_machine=create_test_vm("vm-x")).clean()


class WordPressConstantModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site = create_wp_site("csite")

    def test_str_url_and_type_default(self):
        c = WordPressConstant.objects.create(site=self.site, name="WP_DEBUG", value="false")
        self.assertEqual(c.value_type, WPConstantTypeChoices.STRING)
        self.assertEqual(str(c), f"{self.site}: WP_DEBUG")
        self.assertIn("/plugins/wordpress/constants/", c.get_absolute_url())

    def test_unique_per_site_name(self):
        WordPressConstant.objects.create(site=self.site, name="DISABLE_WP_CRON", value="true", value_type=WPConstantTypeChoices.BOOL)
        with self.assertRaises(IntegrityError), transaction.atomic():
            WordPressConstant.objects.create(site=self.site, name="DISABLE_WP_CRON", value="true")

    def test_same_name_different_site_allowed(self):
        other = create_wp_site("csite2")
        WordPressConstant.objects.create(site=self.site, name="WP_MEMORY_LIMIT", value="256M")
        WordPressConstant.objects.create(site=other, name="WP_MEMORY_LIMIT", value="512M")
        self.assertEqual(WordPressConstant.objects.filter(name="WP_MEMORY_LIMIT").count(), 2)


class WordPressPluginThemeModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site = create_wp_site("psite")

    def test_plugin_defaults_str_url(self):
        p = WordPressPlugin.objects.create(site=self.site, slug="woocommerce")
        self.assertEqual(p.state, PluginStateChoices.ACTIVE)
        self.assertEqual(p.get_state_color(), "green")
        self.assertEqual(p.source, PluginSourceChoices.WPORG)
        self.assertEqual(str(p), f"{self.site}: woocommerce")
        self.assertIn("/plugins/wordpress/plugins/", p.get_absolute_url())

    def test_plugin_absent_state(self):
        p = WordPressPlugin.objects.create(site=self.site, slug="w3-total-cache", state=PluginStateChoices.ABSENT)
        self.assertEqual(p.state, PluginStateChoices.ABSENT)
        self.assertEqual(p.get_state_color(), "red")

    def test_plugin_unique_per_site_slug(self):
        WordPressPlugin.objects.create(site=self.site, slug="jetpack")
        with self.assertRaises(IntegrityError), transaction.atomic():
            WordPressPlugin.objects.create(site=self.site, slug="jetpack")

    def test_theme_defaults_and_url(self):
        t = WordPressTheme.objects.create(site=self.site, slug="twentytwentyfour", source=PluginSourceChoices.ZIP, source_url="https://example.com/t.zip")
        self.assertEqual(t.state, PluginStateChoices.PRESENT_INACTIVE)
        self.assertEqual(t.get_state_color(), "gray")
        self.assertEqual(t.get_source_color(), "gray")
        self.assertEqual(str(t), f"{self.site}: twentytwentyfour")
        self.assertIn("/plugins/wordpress/themes/", t.get_absolute_url())

    def test_theme_unique_per_site_slug(self):
        WordPressTheme.objects.create(site=self.site, slug="astra")
        with self.assertRaises(IntegrityError), transaction.atomic():
            WordPressTheme.objects.create(site=self.site, slug="astra")

    def test_cascade_on_site_delete(self):
        site = create_wp_site("cascade")
        WordPressPlugin.objects.create(site=site, slug="p1")
        WordPressTheme.objects.create(site=site, slug="t1")
        WordPressConstant.objects.create(site=site, name="K", value="v")
        site.delete()
        self.assertEqual(WordPressPlugin.objects.filter(slug="p1").count(), 0)
        self.assertEqual(WordPressTheme.objects.filter(slug="t1").count(), 0)
        self.assertEqual(WordPressConstant.objects.filter(name="K").count(), 0)


class WordPressContentDirectoryModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site = create_wp_site("cdsite")

    def test_defaults_str_url_color(self):
        cd = WordPressContentDirectory.objects.create(site=self.site)
        self.assertEqual(cd.content_dir, "/var/www/html/wp-content")
        self.assertEqual(cd.relocation_state, RelocationStateChoices.IN_PLACE)
        self.assertEqual(cd.get_relocation_state_color(), "gray")
        self.assertEqual(str(cd), f"{self.site}: /var/www/html/wp-content")
        self.assertIn("/plugins/wordpress/content-directories/", cd.get_absolute_url())

    def test_relocating_state(self):
        cd = WordPressContentDirectory.objects.create(
            site=self.site, target_content_dir="/srv/wp-content", relocation_state=RelocationStateChoices.RELOCATING
        )
        self.assertEqual(cd.get_relocation_state_color(), "orange")
        self.assertEqual(cd.target_content_dir, "/srv/wp-content")

    def test_one_to_one_per_site(self):
        WordPressContentDirectory.objects.create(site=self.site)
        with self.assertRaises(IntegrityError), transaction.atomic():
            WordPressContentDirectory.objects.create(site=self.site)
