# SPDX-License-Identifier: AGPL-3.0-or-later
"""Choice sets for the WordPress app-config models. Values match the on-target tokens (plugin/theme
source, wp-config define value type, content-relocation lifecycle, PHP-FPM traffic tier) verbatim."""
from utilities.choices import ChoiceSet


class PluginSourceChoices(ChoiceSet):
    """Where a plugin/theme artifact is fetched from."""
    WPORG = "wporg"
    URL = "url"
    ZIP = "zip"
    CHOICES = [
        (WPORG, "WordPress.org", "blue"),
        (URL, "URL", "cyan"),
        (ZIP, "ZIP upload", "gray"),
    ]


class WPConstantTypeChoices(ChoiceSet):
    """How a ``wp-config.php`` ``define()`` value is emitted: quoted string, bare bool/int, or raw PHP."""
    STRING = "string"
    BOOL = "bool"
    INT = "int"
    RAW = "raw"
    CHOICES = [
        (STRING, "String", "blue"),
        (BOOL, "Boolean", "green"),
        (INT, "Integer", "purple"),
        (RAW, "Raw PHP", "orange"),
    ]


class RelocationStateChoices(ChoiceSet):
    """Lifecycle of the WP content-directory relocation the tofu-wordpress provider performs."""
    IN_PLACE = "in_place"
    RELOCATING = "relocating"
    RELOCATED = "relocated"
    CHOICES = [
        (IN_PLACE, "In place", "gray"),
        (RELOCATING, "Relocating", "orange"),
        (RELOCATED, "Relocated", "green"),
    ]


class FPMProfileChoices(ChoiceSet):
    """PHP-FPM + OPcache traffic-tier profile (low/medium/high). Sized data-driven from the live
    fleet's 30-day Proxmox RRD + Apache pageviews; workers track cacheability, not raw pageviews."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CHOICES = [
        (LOW, "Low", "green"),
        (MEDIUM, "Medium", "blue"),
        (HIGH, "High", "orange"),
    ]
