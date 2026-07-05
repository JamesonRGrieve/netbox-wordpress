# SPDX-License-Identifier: AGPL-3.0-or-later
"""netbox-wordpress: NetBox as the **native source of truth for WordPress application-level
config** — the ``wp-config.php`` constants, the plugin/theme install-state, the WP content-
directory location (and relocation intent), and the per-site PHP-FPM / memory tuning the live
fleet today records only in playbook comments and host_vars.

netbox-wordpress **composes rather than re-models**. The running WordPress service is a
:class:`netbox_services.ServiceInstance` and its HA pairing is a :class:`netbox_services.HAMirror`
(catalog ``wordpress``, ``ha_strategy`` ``content_rsync``) — reused as-is, never duplicated. The
backing database + DB user are :class:`netbox_database.Database` / :class:`netbox_database.DatabaseUser`
records; this plugin only *references* them by FK. Both are hard dependencies, so ``required_plugins``
lists ``netbox_services`` and ``netbox_database`` and the plugin fails fast at startup if either is absent.

**Secret policy (load-bearing):** the WordPress AUTH salts live in OpenBao and are referenced by
``WordPressSite.salt_ref`` (a path key, never the salt values); the DB password lives in
``netbox_database.DatabaseUser.credential_ref`` (also an OpenBao path). Secret *values* never live here.

The ``tofu-wordpress`` provider reads this plugin's REST API as its source of truth — including the
content-relocation contract realized by :class:`WordPressContentDirectory`.
"""
from netbox.plugins import PluginConfig

__version__ = "0.0.1"


class NetBoxWordPressConfig(PluginConfig):
    name = "netbox_wordpress"
    verbose_name = "NetBox WordPress"
    description = "Native SoT for WordPress app config — wp-config constants, plugin/theme state, content dir, per-site tuning"
    version = __version__
    author = "Jameson"
    base_url = "wordpress"
    min_version = "4.6.0"
    max_version = "4.6.99"
    # WordPressSite composes ServiceInstance (HA via HAMirror) + netbox-database Database/DatabaseUser;
    # both are hard dependencies, so failing fast at startup is correct — the netbox-ai pattern.
    required_plugins = ["netbox_services", "netbox_database"]


config = NetBoxWordPressConfig
