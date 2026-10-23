# SPDX-License-Identifier: AGPL-3.0-or-later
"""Native WordPress app-config models. :class:`WordPressSite` is the instance (host-bound + linked to
its ServiceInstance / Database / DatabaseUser); the repeating and long-tail config hangs off it as
child rows (constants, options, plugins, mu-plugins, themes) plus a 1:1 content-directory record.

COMPOSE, DON'T RE-MODEL: the running service, its HA mirror, and the backing DB live in
netbox-services / netbox-database and are referenced by FK — never duplicated here (see DESIGN.md).

SECRET POLICY: AUTH salts are an OpenBao path in ``WordPressSite.salt_ref`` (never the salt values);
the DB password lives in ``netbox_database.DatabaseUser.credential_ref``. Secret values never live here.
"""
import json

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from .choices import (
    FPMProfileChoices, PluginSourceChoices, PluginStateChoices, RelocationStateChoices,
    WPConstantTypeChoices, WPOptionFormatChoices,
)

DEFAULT_TABLE_PREFIX = "wp_"
DEFAULT_CONTENT_DIR = "/var/www/html/wp-content"
DEFAULT_LOGIN_PATH = "wp-login.php"
MUPLUGIN_NAME_VALIDATOR = RegexValidator(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*\.php$", "A bare .php file name (no slashes)."
)
REPO_RELATIVE_PATH_VALIDATOR = RegexValidator(
    r"^(?!/)(?!(?:.*/)?\.\.(?:/|$)).+$", "A repo-relative path: no leading / and no .. segments."
)
SHA256_VALIDATOR = RegexValidator(r"^[0-9a-f]{64}$", "Lowercase hex sha256 (64 chars).")
REPOSITORY_VALIDATOR = RegexValidator(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$", "<Org>/<repo>, e.g. TheBraCoach/bracoach-square-sync.")
COMMIT_VALIDATOR = RegexValidator(r"^[0-9a-f]{40}$", "A full lowercase 40-hex commit id.")


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
    login_slug = models.CharField(
        max_length=64, blank=True,
        help_text="Hidden-login slug (wps-hide-login whl_page); blank = default wp-login.php.",
    )
    install_path = models.CharField(
        max_length=255, blank=True,
        help_text="WP core / Apache DocumentRoot path (e.g. /var/www/html); blank = provider docroot "
        "default. A change is a whole-install relocation the provider performs safely.",
    )
    object_cache_instance = models.ForeignKey(
        "netbox_services.ServiceInstance", on_delete=models.PROTECT, null=True, blank=True,
        related_name="wordpress_object_cache_sites",
        help_text="Backing object-cache (Valkey/Redis) service instance; the WP_REDIS_* constants target it.",
    )
    safe_opt = models.BooleanField(
        default=False,
        help_text="PHP safe-opt hardening: disable_functions, allow_url_fopen off, Action Scheduler "
        "async-runner off, OPcache.",
    )
    trusted_proxies = models.CharField(
        max_length=255, blank=True,
        help_text="Comma-separated trusted proxy IPs/CIDRs for mod_remoteip (e.g. the HAProxy IP); "
        "applied when prod_hardening.",
    )
    enable_hsts = models.BooleanField(
        default=False,
        help_text="Emit the HSTS header — explicit per-site opt-in, only after the cert chain is confirmed.",
    )
    site_icon_url = models.URLField(
        blank=True,
        help_text="Source image for the WordPress Site Icon (favicon/app icon): a square PNG, at least "
        "512px. The provider imports it into the media library and sets it as the icon; blank = unmanaged.",
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


class WordPressOption(NetBoxModel):
    """One declared ``wp_options`` value: plugin settings and site options that are not install-state.
    A blank ``key_path`` manages the whole option (``wp option update``); a dotted ``key_path`` manages
    one nested key of a structured option (``wp option patch update``), e.g. ``wpseo`` /
    ``enable_xml_sitemap``, leaving the rest of the array untouched. ``value_format`` says whether
    ``value`` is a scalar string or JSON."""

    site = models.ForeignKey(WordPressSite, on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=191, help_text="Option name (wp_options.option_name), e.g. wpseo.")
    key_path = models.CharField(
        max_length=255, blank=True,
        help_text="Dotted path to one nested key of a structured option (e.g. enable_xml_sitemap); "
        "blank = the whole option.",
    )
    value = models.TextField(help_text="Declared value (a string, or JSON when value_format is json).")
    value_format = models.CharField(
        max_length=8, choices=WPOptionFormatChoices, default=WPOptionFormatChoices.STRING
    )

    class Meta:
        ordering = ["site", "name", "key_path"]
        verbose_name = "WordPress Option"
        constraints = [
            models.UniqueConstraint(
                fields=["site", "name", "key_path"],
                name="netbox_wordpress_wordpressoption_unique_site_name_key",
            ),
        ]

    def __str__(self):
        return f"{self.site}: {self.name}{'.' + self.key_path if self.key_path else ''}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_wordpress:wordpressoption", args=[self.pk])

    def get_value_format_color(self):
        return WPOptionFormatChoices.colors.get(self.value_format)

    def clean(self):
        super().clean()
        if self.value_format == WPOptionFormatChoices.JSON:
            try:
                json.loads(self.value)
            except ValueError as e:
                raise ValidationError({"value": f"value_format is json but value does not parse: {e}"})


class WordPressPlugin(NetBoxModel):
    """Declared install-state for one WordPress plugin. Blank ``version`` tracks latest; ``source``
    selects wporg / a URL / an uploaded zip (``source_url`` carries the URL or zip location) / OMG's
    Forgejo: ``repository`` at the pinned ``commit``, installed from that commit's archive (the commit
    is the version, so ``version`` and ``source_url`` stay blank)."""

    site = models.ForeignKey(WordPressSite, on_delete=models.CASCADE, related_name="plugins")
    slug = models.CharField(max_length=128, help_text="Plugin slug, e.g. woocommerce.")
    version = models.CharField(max_length=32, blank=True, help_text="Pinned version (blank = track latest).")
    state = models.CharField(
        max_length=16, choices=PluginStateChoices, default=PluginStateChoices.ACTIVE,
        help_text="Declared install-state: absent (remove) / present_inactive / active.",
    )
    source = models.CharField(
        max_length=8, choices=PluginSourceChoices, default=PluginSourceChoices.WPORG
    )
    source_url = models.URLField(blank=True, help_text="Fetch URL for url/zip sources.")
    repository = models.CharField(
        max_length=200, blank=True, validators=[REPOSITORY_VALIDATOR],
        help_text="Forgejo source: the repository, <Org>/<repo>.",
    )
    commit = models.CharField(
        max_length=40, blank=True, validators=[COMMIT_VALIDATOR],
        help_text="Forgejo source: the pinned commit id (full 40 hex).",
    )

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

    def get_state_color(self):
        return PluginStateChoices.colors.get(self.state)

    def clean(self):
        super().clean()
        if self.source == PluginSourceChoices.FORGEJO:
            errors = {f: "Required for a Forgejo source." for f in ("repository", "commit") if not getattr(self, f)}
            errors |= {
                f: "Leave blank for a Forgejo source (the commit pins the code)."
                for f in ("version", "source_url") if getattr(self, f)
            }
        else:
            errors = {f: "Only used by a Forgejo source." for f in ("repository", "commit") if getattr(self, f)}
        if errors:
            raise ValidationError(errors)


class WordPressMuPlugin(NetBoxModel):
    """One site-specific must-use plugin file. The code lives in OMG's Forgejo: ``source_path`` in
    ``repository`` at the pinned ``commit``. NetBox declares which site gets which file at which commit;
    the pipeline installs that file's exact bytes (checked against ``sha256``) to
    ``wp-content/mu-plugins/<name>``."""

    site = models.ForeignKey(WordPressSite, on_delete=models.CASCADE, related_name="muplugins")
    name = models.CharField(
        max_length=128, validators=[MUPLUGIN_NAME_VALIDATOR],
        help_text="File name in wp-content/mu-plugins/, e.g. bracoach-square-guard.php.",
    )
    repository = models.CharField(
        max_length=200, validators=[REPOSITORY_VALIDATOR],
        help_text="Forgejo repository holding the file, <Org>/<repo>.",
    )
    commit = models.CharField(
        max_length=40, validators=[COMMIT_VALIDATOR], help_text="Pinned commit id (full 40 hex)."
    )
    source_path = models.CharField(
        max_length=255, validators=[REPO_RELATIVE_PATH_VALIDATOR],
        help_text="Path of the file inside the repository (no leading /, no ..).",
    )
    sha256 = models.CharField(
        max_length=64, validators=[SHA256_VALIDATOR], help_text="Lowercase hex sha256 of the file's exact bytes."
    )
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["site", "name"]
        verbose_name = "WordPress Must-Use Plugin"
        constraints = [
            models.UniqueConstraint(
                fields=["site", "name"],
                name="netbox_wordpress_wordpressmuplugin_unique_site_name",
            ),
        ]

    def __str__(self):
        return f"{self.site}: {self.name}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_wordpress:wordpressmuplugin", args=[self.pk])


class WordPressTheme(NetBoxModel):
    """Declared install-state for one WordPress theme. Only one theme is ``active`` at a time on a
    site (``state`` defaults ``present_inactive``); ``source``/``source_url`` mirror
    :class:`WordPressPlugin`."""

    site = models.ForeignKey(WordPressSite, on_delete=models.CASCADE, related_name="themes")
    slug = models.CharField(max_length=128, help_text="Theme slug, e.g. twentytwentyfour.")
    version = models.CharField(max_length=32, blank=True, help_text="Pinned version (blank = track latest).")
    state = models.CharField(
        max_length=16, choices=PluginStateChoices, default=PluginStateChoices.PRESENT_INACTIVE,
        help_text="Declared install-state: absent (remove) / present_inactive / active (current theme).",
    )
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

    def get_state_color(self):
        return PluginStateChoices.colors.get(self.state)


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
