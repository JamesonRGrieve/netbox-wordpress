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
    WPOptionFormatChoices,
)
from netbox_wordpress.models import (
    WordPressConstant, WordPressContentDirectory, WordPressMuPlugin, WordPressOption, WordPressPlugin,
    WordPressSite, WordPressTheme,
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

    def test_site_icon_url_defaults_blank_and_persists(self):
        s = WordPressSite.objects.create(name="iconic", device=create_test_device("d-icon"))
        self.assertEqual(s.site_icon_url, "")
        s.site_icon_url = "https://cdn.example/icons/iconic-512.png"
        s.save()
        s.refresh_from_db()
        self.assertEqual(s.site_icon_url, "https://cdn.example/icons/iconic-512.png")

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


class WordPressOptionModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site = create_wp_site("osite")

    def test_whole_option_defaults_str_url(self):
        o = WordPressOption.objects.create(site=self.site, name="blog_public", value="1")
        self.assertEqual(o.key_path, "")
        self.assertEqual(o.value_format, WPOptionFormatChoices.STRING)
        self.assertEqual(o.get_value_format_color(), "blue")
        self.assertEqual(str(o), f"{self.site}: blog_public")
        self.assertIn("/plugins/wordpress/options/", o.get_absolute_url())

    def test_nested_key_str(self):
        o = WordPressOption.objects.create(
            site=self.site, name="wpseo", key_path="enable_xml_sitemap", value="true",
            value_format=WPOptionFormatChoices.JSON,
        )
        self.assertEqual(str(o), f"{self.site}: wpseo.enable_xml_sitemap")

    def test_unique_per_site_name_key_path(self):
        WordPressOption.objects.create(site=self.site, name="wpseo", key_path="a", value="1")
        WordPressOption.objects.create(site=self.site, name="wpseo", key_path="b", value="1")
        with self.assertRaises(IntegrityError), transaction.atomic():
            WordPressOption.objects.create(site=self.site, name="wpseo", key_path="a", value="2")

    def test_same_option_different_site_allowed(self):
        other = create_wp_site("osite2")
        WordPressOption.objects.create(site=self.site, name="blogdescription", value="x")
        WordPressOption.objects.create(site=other, name="blogdescription", value="y")
        self.assertEqual(WordPressOption.objects.filter(name="blogdescription").count(), 2)

    def test_clean_json_value_must_parse(self):
        bad = WordPressOption(site=self.site, name="wpseo", key_path="k", value="{not json", value_format=WPOptionFormatChoices.JSON)
        with self.assertRaises(ValidationError):
            bad.clean()
        WordPressOption(site=self.site, name="wpseo", key_path="k", value='{"a": [1, 2]}', value_format=WPOptionFormatChoices.JSON).clean()

    def test_clean_string_value_not_parsed(self):
        WordPressOption(site=self.site, name="blogname", value="{not json").clean()  # no raise

    def test_cascade_with_site(self):
        s = create_wp_site("osite-cascade")
        WordPressOption.objects.create(site=s, name="blog_public", value="0")
        s.delete()
        self.assertFalse(WordPressOption.objects.filter(site__name="osite-cascade").exists())


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


SHA = "a" * 64
GUARD_PATH = "bracoach-square-guard.php"
REPO = "TheBraCoach/bracoach-square-sync"
COMMIT = "6cfae4c" + "0" * 33


class WordPressMuPluginModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site = create_wp_site("thebracoach.ca")

    def _mu(self, **kw):
        return WordPressMuPlugin(**{"site": self.site, "name": "bracoach-square-guard.php", "repository": REPO, "commit": COMMIT,
                                     "source_path": GUARD_PATH, "sha256": SHA, **kw})

    def _assert_invalid(self, field, **kw):
        with self.assertRaises(ValidationError) as cm:
            self._mu(**kw).full_clean()
        self.assertIn(field, cm.exception.message_dict)

    def test_create_str_url(self):
        m = self._mu(description="Square catalogue guard")
        m.full_clean()
        m.save()
        m.refresh_from_db()
        self.assertEqual(m.sha256, SHA)
        self.assertEqual((m.repository, m.commit, m.source_path), (REPO, COMMIT, GUARD_PATH))
        self.assertEqual(str(m), "thebracoach.ca: bracoach-square-guard.php")
        self.assertIn("/plugins/wordpress/muplugins/", m.get_absolute_url())
        self.assertEqual(list(self.site.muplugins.all()), [m])

    def test_unique_per_site_name(self):
        self._mu().save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._mu(sha256="b" * 64).save()

    def test_same_name_different_site_allowed(self):
        self._mu().save()
        self._mu(site=create_wp_site("mu-other")).save()
        self.assertEqual(WordPressMuPlugin.objects.filter(name="bracoach-square-guard.php").count(), 2)

    def test_name_validator(self):
        for bad in ("guard.js", "sub/guard.php", "../guard.php", ".hidden.php", "guard.php.bak", "gu ard.php", ""):
            self._assert_invalid("name", name=bad)
        self._mu(name="Zz_9.guard-v2.php").full_clean()

    def test_source_path_validator(self):
        for bad in ("/abs/guard.php", "../guard.php", "a/../guard.php", "a/..", "..", ""):
            self._assert_invalid("source_path", source_path=bad)
        self._mu(source_path="files/guard..v2.php").full_clean()

    def test_repository_validator(self):
        for bad in ("bracoach-square-sync", "a/b/c", "/a/b", "a/", "a b/c", ""):
            self._assert_invalid("repository", repository=bad)
        self._mu(repository="ObsessedMediaGroup/woocommerce-square-guard").full_clean()

    def test_commit_validator(self):
        for bad in ("6cfae4c", "A" * 40, "g" * 40, "a" * 41, "main", ""):
            self._assert_invalid("commit", commit=bad)

    def test_sha256_validator(self):
        for bad in ("A" * 64, "a" * 63, "g" * 64, ""):
            self._assert_invalid("sha256", sha256=bad)

    def test_cascade_on_site_delete(self):
        s = create_wp_site("mu-cascade")
        self._mu(site=s).save()
        s.delete()
        self.assertFalse(WordPressMuPlugin.objects.filter(site__name="mu-cascade").exists())
