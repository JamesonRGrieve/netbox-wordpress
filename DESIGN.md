<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# netbox-wordpress — Design

`netbox-wordpress` is the native NetBox 4.6 source of truth for **WordPress application-level
config**. Everything a WordPress install needs beyond "a host, a service, and a database" —
the `wp-config.php` constants, the plugin/theme install-state, the content-directory location
and relocation intent, and the per-site PHP-FPM / memory tuning — becomes a real, queryable,
change-logged NetBox object instead of living in `wp-config.php`, playbook comments, and
`host_vars`. The `tofu-wordpress` provider reads this plugin's REST API as its SoT.

## 1. Model diagram

```
                       netbox_services                 netbox_database
                       ┌─────────────────┐             ┌──────────────┐  ┌───────────────┐
                       │ ServiceInstance │             │  Database    │  │ DatabaseUser  │
                       └────────▲────────┘             └──────▲───────┘  └───────▲───────┘
                                │ FK (PROTECT, null)          │ FK          FK   │
   dcim.Device ◄──┐             │                             │                  │
                  │ FK(PROTECT, │       ┌─────────────────────┴──────────────────┘
 virtualization.  │  null; XOR  │       │
   VirtualMachine ◄── exactly one via clean())
                  │             │       │
              ┌───┴─────────────┴───────┴──────────────────────────────────────┐
              │                      WordPressSite                              │
              │  name(unique) site_url wp_version table_prefix is_multisite     │
              │  install_path fpm_profile wp_memory_limit prod_hardening        │
              │  safe_opt login_slug trusted_proxies enable_hsts salt_ref(Bao)  │
              └───┬───────────────┬──────────────────┬───────────────┬─────────┘
        constants │        plugins │           themes │  content_dir  │ (1:1)
          (FK)    │          (FK)  │            (FK)   │      (O2O)    │
     ┌────────────▼──┐ ┌───────────▼──┐ ┌──────────────▼┐ ┌────────────▼──────────────┐
     │WordPressConst.│ │WordPressPlugin│ │WordPressTheme │ │ WordPressContentDirectory │
     │ name value    │ │ slug version  │ │ slug version  │ │ content_dir uploads_dir   │
     │ value_type    │ │ state         │ │ state         │ │ target_content_dir        │
     │ U(site,name)  │ │ source src_url│ │ source src_url│ │ content_url               │
     │               │ │ U(site,slug)  │ │ U(site,slug)  │ │ relocation_state          │
     └───────────────┘ └───────────────┘ └───────────────┘ └───────────────────────────┘
```

Child rows CASCADE with their `WordPressSite`. The five composed FKs (device, virtual_machine,
service_instance, database, db_user) are `PROTECT` — you cannot delete a host/service/DB while a
WordPress site still references it.

## 2. The compose boundary — nothing is duplicated

This plugin owns **only** WordPress *app* config. Everything structural is referenced, not
re-modeled:

- **The running service** is a `netbox_services.ServiceInstance` (catalog `wordpress`).
  `WordPressSite.service_instance` FKs it. Status, listeners/ports, OpenBao paths for
  service-level creds — all already modeled there.
- **HA (primary↔mirror)** is `netbox_services.HAMirror` — reused **as-is, no new model**. Its
  docstring literally describes "the mirror WordPress → the primary WordPress"; the reconciler
  reads `mirror.catalog.ha_strategy` (`content_rsync` for WordPress). Expressing WP HA here
  would duplicate a working primitive, so we do not. A WordPress HA pair is two ServiceInstances
  (each with its own WordPressSite) joined by one HAMirror row.
- **The database + user** are `netbox_database.Database` / `netbox_database.DatabaseUser`.
  `WordPressSite.database` / `.db_user` FK them. The DB engine (MariaDB), charset, host, port,
  and the DB **password** (`DatabaseUser.credential_ref` → OpenBao) live there — this plugin
  never restates them.

`required_plugins = ["netbox_services", "netbox_database"]` makes both hard dependencies that
fail fast at startup (the netbox-ai pattern), and the migration depends on each sibling's
`0001_initial` so the FK target tables exist before ours are built.

## 3. The fleet-tuning story — comments become columns

The live 301–321 WordPress FPM fleet is tuned by a `wordpress_fpm_profile` (low / medium /
high) recorded today only in the `install_wordpress.yml` header and per-host `host_vars`:

| profile | workers | memory_limit | opcache   | min CT RAM | use                         |
|---------|---------|--------------|-----------|------------|-----------------------------|
| low     | 5       | 256M         | 128M/10k  | 2 GB       | page-cached brochures       |
| medium  | 8       | 512M         | 192M/16k  | 2 GB       | active commerce (uncacheable) |
| high    | 20      | 512M         | 256M/20k  | 3 GB       | busy commerce / seasonal peak |

`WordPressSite.fpm_profile` (choice) + `wp_memory_limit` promote that tiering into NetBox: the
tier is now a queryable field the reconciler reads, not a comment an operator must remember to
copy into host_vars. `prod_hardening` is the single umbrella toggle from the playbook that flips
the whole production server-security layer (`FORCE_SSL_ADMIN`, fail2ban, mod_remoteip, unattended
upgrades, AIDE, rkhunter).

## 3a. Per-site security, login, docroot & cache — the values a bool can't hold

The hardening layer is not purely a switch — it carries per-site values and infra-load-bearing
knobs the fleet records in `host_vars` today. These are promoted to typed `WordPressSite` fields so
the provider and the login/health checks read one SoT:

- **`login_slug`** — the wps-hide-login `whl_page` (a plugin *option*, not install-state). The login
  health check must hit this slug; keeping it here removes the split-brain where NetBox owned the
  site but `host_vars` owned the slug. Blank ⇒ default `wp-login.php`.
- **`install_path`** — the WP core / Apache `DocumentRoot` (e.g. `/var/www/html`). The fleet's tteck
  CTs install at `/var/www/html/wordpress`; normalizing to `/var/www/html` is a **whole-install
  relocation** distinct from the `wp-content` move in §5 — the provider performs it safely (quiesce →
  move core → repoint the vhost + WP_HOME/SITEURL → health → rollback). Blank ⇒ the provider docroot
  default.
- **`safe_opt`** — the PHP execution-hardening layer (`disable_functions`, `allow_url_fopen` off,
  Action Scheduler `async-runner` off, OPcache), matching the playbook's `wordpress_safe_opt`. A
  distinct concern from `prod_hardening` (server security), so a distinct toggle.
- **`trusted_proxies`** — comma-separated proxy IPs/CIDRs for `mod_remoteip` (e.g. the HAProxy IP);
  applied under `prod_hardening`. A bool can't carry the address, so it is its own field.
- **`enable_hsts`** — an **explicit per-site opt-in** (default off). Turning HSTS on before the cert
  chain is proven is a footgun, so it never rides the `prod_hardening` bool.
- **`object_cache_instance`** — a `PROTECT` FK to the backing Valkey/Redis
  `netbox_services.ServiceInstance`. The `WP_REDIS_*` constants still carry the address for the
  provider, but the FK makes the cache backend a first-class, queryable relationship (you cannot
  delete a cache instance a site still points at).

## 4. wp-config constants — typed fields vs rows

The universal, always-present knobs are **typed fields** on `WordPressSite`: `table_prefix`
(`$table_prefix`), `is_multisite` (`WP_ALLOW_MULTISITE`/`MULTISITE`), `wp_memory_limit`
(`WP_MEMORY_LIMIT`), and — via `prod_hardening` — the hardening bundle. Everything else in the
real `wp-config.php.j2` is the **long tail**, modeled as `WordPressConstant` rows with a
`value_type` (string / bool / int / raw) that tells the provider how to emit the `define()`.

Well-known toggles have **documented fleet defaults** (from `wp-config.php.j2`) and are stored as
rows only when a site overrides the default:

| Constant                | Fleet default | Notes                                              |
|-------------------------|---------------|----------------------------------------------------|
| `DISALLOW_FILE_EDIT`    | `true`        | Block wp-admin code editing.                       |
| `WP_AUTO_UPDATE_CORE`   | `'minor'`     | Self-apply minor security releases.                |
| `DISABLE_WP_CRON`       | `true`        | System cron replaces wp-cron (`*/5` default).      |
| `WP_DEBUG` / `_LOG`     | `false`       | On only when `wordpress_debug`.                    |
| `WP_DEBUG_DISPLAY`      | `false`       | Never leak debug output to visitors.               |
| `WP_POST_REVISIONS`     | `5`           | Limit revision DB bloat.                           |
| `EMPTY_TRASH_DAYS`      | `7`           | (WP default is 30.)                                |
| `FORCE_SSL_ADMIN`       | `prod_hardening` | Pairs with the X-Forwarded-Proto trust block.   |
| `WP_REDIS_*`            | object-cache on | Valkey/Redis object cache; per-CT local Valkey.  |
| `WP_CACHE`              | page-cache on | Cache Enabler full-page cache.                     |

`DISALLOW_FILE_MODS` is deliberately **not** set (it would block the plugin/theme auto-updates
`WP_AUTO_UPDATE_CORE='minor'` relies on). The `X-Forwarded-Proto` trust snippet is provider
boilerplate, not config, so it is not modeled.

## 5. The content-relocation contract

`WordPressContentDirectory` (1:1 with a site) is the SoT for the tofu-wordpress content-directory
relocation feature. `content_dir` is the *current* `WP_CONTENT_DIR`; `target_content_dir` is the
*desired* one. When `target_content_dir` is set and differs from `content_dir`, the provider
performs a **safe relocation**, tracked by `relocation_state`:

```
in_place ──▶ relocating ──▶ relocated
```

Contract the provider realizes:

1. **Quiesce** — maintenance mode / stop the FPM workers so no writes race the move.
2. **Move + verify** — copy `content_dir` → `target_content_dir`, verify the copy (counts/checksums).
3. **Rewrite defines** — update `WP_CONTENT_DIR` / `WP_CONTENT_URL` (and the uploads path).
4. **Symlink + health** — symlink the old path to the new one and run a real health check.
5. **Rollback on failure** — revert the defines and point back at `content_dir`; leave state usable.

On success the provider sets `content_dir = target_content_dir` and `relocation_state = relocated`.
NetBox holds the *intent* and the *observed state*; the provider owns the mechanism.

## 6. Secret-ref policy

No secret value is ever stored. `WordPressSite.salt_ref` is an **OpenBao path** to the eight WP
AUTH salts (`AUTH_KEY`, `SECURE_AUTH_KEY`, … `NONCE_SALT`) — never the salt strings. The DB
password is not here at all: it lives in `netbox_database.DatabaseUser.credential_ref` (also an
OpenBao path). NetBox holds structure; OpenBao holds secrets.

## 7. Consumer note

`tofu-wordpress` is the downstream consumer. It reads the REST API (`/api/plugins/wordpress/…`)
as the single source of truth: `WordPressSite` (host + service + DB + tuning) → renders the FPM
pool + `wp-config.php`; `WordPressConstant` rows → the long-tail `define()`s; `WordPressPlugin`
/ `WordPressTheme` `state` → `wp plugin/theme` install-state — `active` installs+activates,
`present_inactive` installs+deactivates, and **`absent` uninstalls** (so the SoT can retire cruft
like W3TC/LiteSpeed, not merely leave it off); `WordPressContentDirectory` → drives the
`wp-content` relocation state machine in §5, and `WordPressSite.install_path` → the whole-install /
Apache-docroot relocation (§3a). HA reconciliation reads `netbox_services.HAMirror`, not this plugin.

## 8. Verification owed

There is no live NetBox in this build host, so the following is **owed** and must be run against
the pinned NetBox 4.6 with netbox-services + netbox-database installed:

- `python manage.py makemigrations netbox_wordpress --check --dry-run` on an ephemeral NetBox
  (confirms the hand-authored `0001_initial` matches the models, and that the cross-plugin FK
  targets `netbox_services.serviceinstance` / `netbox_database.database` / `.databaseuser`
  resolve).
- Full test run: `python /opt/netbox/app/netbox/manage.py test netbox_wordpress --keepdb -v2`.

`py_compile` passes on all package modules in this build host (the only static gate available here).
