# SPDX-License-Identifier: AGPL-3.0-or-later
"""Native WordPress app-config models. :class:`WordPressSite` is the instance (host-bound + linked to
its ServiceInstance / Database / DatabaseUser); the repeating and long-tail config hangs off it as
child rows (constants, plugins, themes) plus a 1:1 content-directory record.

COMPOSE, DON'T RE-MODEL: the running service, its HA mirror, and the backing DB live in
netbox-services / netbox-database and are referenced by FK — never duplicated here (see DESIGN.md).

SECRET POLICY: AUTH salts are an OpenBao path in ``WordPressSite.salt_ref`` (never the salt values);
the DB password lives in ``netbox_database.DatabaseUser.credential_ref``. Secret values never live here.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from .choices import (
    FPMProfileChoices, PluginSourceChoices, RelocationStateChoices, WPConstantTypeChoices,
)

DEFAULT_TABLE_PREFIX = "wp_"
DEFAULT_CONTENT_DIR = "/var/www/html/wp-content"


class WordPressSite(NetBoxModel):
    """One WordPress install. Host-bound to exactly one of a ``dcim.Device`` or a
    ``virtualization.VirtualMachine`` (enforced by :meth:`clean`), linked to the running
    ``netbox_services.ServiceInstance`` and to its backing ``netbox_database`` records. The typed
    fields here are the universal per-site knobs (table prefix, multisite, FPM tier, memory limit,
    prod-hardening umbrella); the long tail of ``wp-config.php`` defines lives in
    :class:`WordPressConstant` rows."""

    name = models.CharField(max_length=128, unique=True, help_text="Unique site identifier.")
    device = models.ForeignKey(
        "dcim.Device", on_delete=models.PROTECT, null=True, blank=True,
        related_name="wordpress_sites", help_text="Host device (mutually exclusive with virtual_machine).",
    )
    virtual_machine = models.ForeignKey(
        "virtualization.VirtualMachine", on_delete=models.PROTECT, null=True, blank=True,
        related_name="wordpress_sites", help_text="Host VM/CT (mutually exclusive with device).",
    )
    service_instance = models.ForeignKey(
        "netbox_services.ServiceInstance", on_delete=models.PROTECT, null=True, blank=True,
        related_name="wordpress_sites", help_text="The running WordPress service instance (netbox-services).",
    )
    site_url = models.URLField(blank=True, help_text="Public site URL (WP_HOME / siteurl).")
    wp_version = models.CharField(max_length=32, blank=True, help_text="Target WordPress core version.")
    table_prefix = models.CharField(
        max_length=64, default=DEFAULT_TABLE_PREFIX, help_text="wp-config $table_prefix."
    )
    is_multisite = models.BooleanField(default=False, help_text="WP Multisite (network) enabled.")
    database = models.ForeignKey(
        "netbox_database.Database", on_delete=models.PROTECT, null=True, blank=True,
        related_name="wordpress_sites", help_text="Backing database (netbox-database).",
    )
    db_user = models.ForeignKey(
        "netbox_database.DatabaseUser", on_delete=models.PROTECT, null=True, blank=True,
        related_name="wordpress_sites", help_text="DB user (netbox-database); password is credential_ref there.",
    )
    fpm_profile = models.CharField(
        max_length=8, choices=FPMProfileChoices, blank=True,
        help_text="PHP-FPM/OPcache traffic tier (low/medium/high) — from the fleet tiering.",
    )
    wp_memory_limit = models.CharField(
        max_length=16, blank=True, help_text="WP_MEMORY_LIMIT, e.g. 256M."
    )
    prod_hardening = models.BooleanField(
        default=False, help_text="Production server-security umbrella (FORCE_SSL_ADMIN, fail2ban, remoteip, …)."
    )
    salt_ref = models.CharField(
        max_length=255, blank=True, help_text="OpenBao path for the AUTH salts — NEVER the salt values."
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "WordPress Site"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:netbox_wordpress:wordpresssite", args=[self.pk])

    def get_fpm_profile_color(self):
        return FPMProfileChoices.colors.get(self.fpm_profile)

    def clean(self):
        super().clean()
        if bool(self.device_id) == bool(self.virtual_machine_id):
            raise ValidationError(
                "A WordPress site must be bound to exactly one of a device or a virtual machine."
            )


class WordPressConstant(NetBoxModel):
    """A single ``wp-config.php`` ``define()`` — the long tail beyond the typed fields on
    :class:`WordPressSite`. ``value_type`` drives how the value is emitted (quoted string, bare
    bool/int, or raw PHP). Well-known toggles (DISABLE_WP_CRON, DISALLOW_FILE_EDIT, …) have
    documented fleet defaults in DESIGN.md and are stored as rows only where a site overrides them."""

    site = models.ForeignKey(WordPressSite, on_delete=models.CASCADE, related_name="constants")
    name = models.CharField(max_length=128, help_text="Constant name, e.g. WP_DEBUG.")
    value = models.CharField(max_length=255, help_text="Constant value (as declared for value_type).")
    value_type = models.CharField(
        max_length=8, choices=WPConstantTypeChoices, default=WPConstantTypeChoices.STRING
    )

    class Meta:
        ordering = ["site", "name"]
        verbose_name = "WordPress Constant"
        constraints = [
            models.UniqueConstraint(
                fields=["site", "name"],
                name="netbox_wordpress_wordpressconstant_unique_site_name",
            ),
        ]

    def __str__(self):
        return f"{self.site}: {self.name}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_wordpress:wordpressconstant", args=[self.pk])

    def get_value_type_color(self):
        return WPConstantTypeChoices.colors.get(self.value_type)


class WordPressPlugin(NetBoxModel):
    """Declared install-state for one WordPress plugin. Blank ``version`` tracks latest; ``source``
    selects wporg / a URL / an uploaded zip (``source_url`` carries the URL or zip location)."""

    site = models.ForeignKey(WordPressSite, on_delete=models.CASCADE, related_name="plugins")
    slug = models.CharField(max_length=128, help_text="Plugin slug, e.g. woocommerce.")
    version = models.CharField(max_length=32, blank=True, help_text="Pinned version (blank = track latest).")
    is_active = models.BooleanField(default=True, help_text="Plugin activated on the site.")
    source = models.CharField(
        max_length=8, choices=PluginSourceChoices, default=PluginSourceChoices.WPORG
    )
    source_url = models.URLField(blank=True, help_text="Fetch URL for url/zip sources.")

    class Meta:
        ordering = ["site", "slug"]
        verbose_name = "WordPress Plugin"
        constraints = [
            models.UniqueConstraint(
                fields=["site", "slug"],
                name="netbox_wordpress_wordpressplugin_unique_site_slug",
            ),
        ]

    def __str__(self):
        return f"{self.site}: {self.slug}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_wordpress:wordpressplugin", args=[self.pk])

    def get_source_color(self):
        return PluginSourceChoices.colors.get(self.source)


class WordPressTheme(NetBoxModel):
    """Declared install-state for one WordPress theme. Only one theme is active at a time on a site
    (``is_active`` defaults False); ``source``/``source_url`` mirror :class:`WordPressPlugin`."""

    site = models.ForeignKey(WordPressSite, on_delete=models.CASCADE, related_name="themes")
    slug = models.CharField(max_length=128, help_text="Theme slug, e.g. twentytwentyfour.")
    version = models.CharField(max_length=32, blank=True, help_text="Pinned version (blank = track latest).")
    is_active = models.BooleanField(default=False, help_text="Theme active (the site's current theme).")
    source = models.CharField(
        max_length=8, choices=PluginSourceChoices, default=PluginSourceChoices.WPORG
    )
    source_url = models.URLField(blank=True, help_text="Fetch URL for url/zip sources.")

    class Meta:
        ordering = ["site", "slug"]
        verbose_name = "WordPress Theme"
        constraints = [
            models.UniqueConstraint(
                fields=["site", "slug"],
                name="netbox_wordpress_wordpresstheme_unique_site_slug",
            ),
        ]

    def __str__(self):
        return f"{self.site}: {self.slug}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_wordpress:wordpresstheme", args=[self.pk])

    def get_source_color(self):
        return PluginSourceChoices.colors.get(self.source)


class WordPressContentDirectory(NetBoxModel):
    """The 1:1 SoT for the tofu-wordpress content-relocation feature.

    ``content_dir`` is the *current* WP_CONTENT_DIR; ``target_content_dir`` is the *desired* path.
    When ``target_content_dir`` is set and differs from ``content_dir``, the tofu-wordpress provider
    performs a SAFE RELOCATION, tracked by ``relocation_state``:

        in_place → relocating → relocated

    Relocation contract realized by tofu-wordpress: quiesce the site (maintenance mode / stop
    workers) → move ``content_dir`` to ``target_content_dir`` and verify the copy → rewrite the
    WP_CONTENT_DIR / WP_CONTENT_URL defines (and uploads path) → symlink the old path and run a
    health check → on any failure, roll back to ``content_dir`` and revert the defines. On success
    the provider sets ``content_dir = target_content_dir`` and ``relocation_state = relocated``."""

    site = models.OneToOneField(
        WordPressSite, on_delete=models.CASCADE, related_name="content_directory"
    )
    content_dir = models.CharField(
        max_length=255, default=DEFAULT_CONTENT_DIR, help_text="Current WP_CONTENT_DIR absolute path."
    )
    uploads_dir = models.CharField(
        max_length=255, blank=True, help_text="Uploads path if custom (blank = default wp-content/uploads)."
    )
    target_content_dir = models.CharField(
        max_length=255, blank=True, help_text="Desired path; when != content_dir the provider relocates."
    )
    content_url = models.CharField(max_length=255, blank=True, help_text="WP_CONTENT_URL.")
    relocation_state = models.CharField(
        max_length=16, choices=RelocationStateChoices, default=RelocationStateChoices.IN_PLACE
    )

    class Meta:
        ordering = ["site"]
        verbose_name = "WordPress Content Directory"

    def __str__(self):
        return f"{self.site}: {self.content_dir}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_wordpress:wordpresscontentdirectory", args=[self.pk])

    def get_relocation_state_color(self):
        return RelocationStateChoices.colors.get(self.relocation_state)
