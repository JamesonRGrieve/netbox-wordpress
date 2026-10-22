<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# netbox-wordpress

A NetBox 4.6 plugin: the **native source of truth for WordPress application-level config** —
the `wp-config.php` constants, the plugin/theme install-state, the content-directory location
(and relocation intent), and the per-site PHP-FPM / memory tuning.

Depends on **netbox-services** (the running service + HA mirror) and **netbox-database** (the
backing DB + user). The `tofu-wordpress` provider reads this plugin's REST API as its SoT.

## Why

WordPress app config today lives in three ill-suited places: `wp-config.php` on the box, the
`install_wordpress.yml` playbook's header comments (the FPM low/medium/high fleet tiering,
`wordpress_prod_hardening`, `wordpress_system_cron_minute`), and per-host `host_vars`. None of
it is queryable, change-logged, or exposed over an API. This plugin gives every knob a real
column so it can be declared in NetBox and reconciled 1:1.

It **composes, never re-models**: the running service is a `netbox_services.ServiceInstance`,
its primary↔mirror HA is a `netbox_services.HAMirror` (catalog `wordpress`, strategy
`content_rsync`), and the database/user are `netbox_database.Database` / `.DatabaseUser`. This
plugin only references them by FK.

## Model

- **WordPressSite** — the install. Host-bound to exactly one of a `dcim.Device` or a
  `virtualization.VirtualMachine` (enforced by `clean()`). Links `service_instance`,
  `object_cache_instance` (Valkey/Redis), `database`, `db_user`. Typed per-site knobs: `site_url`,
  `wp_version`, `table_prefix`, `is_multisite`, `install_path` (WP core / Apache docroot),
  `fpm_profile` (low/medium/high), `wp_memory_limit`, `prod_hardening`, `safe_opt` (PHP hardening),
  `login_slug` (wps-hide-login), `trusted_proxies`, `enable_hsts`, `salt_ref` (OpenBao path —
  never the salts), `site_icon_url` (the Site Icon's source image; the provider imports it).
  - **WordPressConstant** (FK) — a single `wp-config.php` `define()` (`name`, `value`,
    `value_type`); unique per `(site, name)`. The long tail beyond the typed fields.
  - **WordPressOption** (FK) — one declared `wp_options` value: the whole option (blank
    `key_path`) or one nested key of a settings array (dotted `key_path`, e.g. `wpseo` /
    `enable_xml_sitemap`); `value_format` string or json. Unique per `(site, name, key_path)`.
  - **WordPressPlugin** (FK) — `slug`, `version` (blank = latest), `state`
    (absent / present_inactive / active — `absent` uninstalls), `source` (wporg/url/zip),
    `source_url`; unique per `(site, slug)`.
  - **WordPressMuPlugin** (FK) — one site-specific must-use plugin: `name` (the `*.php` file
    written to `wp-content/mu-plugins/`), `repository` (Forgejo `<Org>/<repo>`), `commit` (pinned
    40-hex id), `source_path` (the file inside that repo), `sha256` (hex hash of its exact bytes),
    `description`; unique per `(site, name)`. The code lives in Forgejo; NetBox pins which site gets
    which file at which commit and hash.
  - **WordPressTheme** (FK) — same shape as plugin (`state` default `present_inactive`); unique
    per `(site, slug)`.
  - **WordPressContentDirectory** (1:1) — the SoT for the tofu-wordpress content-relocation
    feature: `content_dir`, `uploads_dir`, `target_content_dir`, `content_url`,
    `relocation_state` (in_place → relocating → relocated).

All models inherit `NetBoxModel` (custom fields, tags, change logging, GraphQL, REST API).

## Secret policy

WordPress AUTH salts live in **OpenBao**, referenced by `WordPressSite.salt_ref` (a path key,
never the values). The DB password lives in `netbox_database.DatabaseUser.credential_ref`.
Secret values never live here.

## Install

```bash
uv pip install --python /opt/netbox/venv/bin/python netbox-wordpress   # after netbox-services + netbox-database
# add "netbox_wordpress" to PLUGINS in configuration.py
python manage.py migrate netbox_wordpress
python manage.py collectstatic --no-input
systemctl restart netbox netbox-rq
```

## Develop / test

Tests run against a **real NetBox test database** (no mocks). See `CLAUDE.md`.

```bash
python /opt/netbox/app/netbox/manage.py test netbox_wordpress --keepdb -v2
```

## License

AGPL-3.0-or-later.
