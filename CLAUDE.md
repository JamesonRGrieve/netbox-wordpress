# netbox-wordpress — Agent Operating Guide

Adapted from the sibling `../netbox-services` / `../netbox-system-services` plugins (same
engineering + test discipline), re-targeted to the **WordPress application layer**.

`netbox-wordpress` is an **AGPL-3.0** NetBox 4.6 plugin: the **native source of truth for
WordPress app config** — the `wp-config.php` constants, plugin/theme install-state, the WP
content-directory location (and relocation intent), and the per-site PHP-FPM / memory tuning
that today live only in `install_wordpress.yml` header comments and `host_vars`. The
`tofu-wordpress` provider reads this plugin's REST API as its SoT. See **DESIGN.md** for the
model diagram, compose boundary, fleet-tuning story, relocation contract, and verification owed.

**Composes, does not re-model.** The running WordPress service is a
`netbox_services.ServiceInstance`; primary↔mirror HA is `netbox_services.HAMirror` (catalog
`wordpress`, `ha_strategy` `content_rsync`) reused **as-is — no HA model here**; the backing DB +
user are `netbox_database.Database` / `netbox_database.DatabaseUser`. This plugin references all
of them by FK. `required_plugins = ["netbox_services", "netbox_database"]` makes both hard
dependencies (fail-fast at startup); the migration depends on each sibling's `0001_initial`.

**Secret policy (load-bearing):** `WordPressSite.salt_ref` is an **OpenBao path** to the WP AUTH
salts — never the salt values. The DB password lives in
`netbox_database.DatabaseUser.credential_ref`, not here. Secret values never live in this plugin.

**No config_context, no JSON data-blob.** Every attribute is a real typed column or a child row.
The long tail of `wp-config.php` defines is `WordPressConstant` rows (typed by `value_type`), not
a blob.

---

## Key Directives / Rules

### DO, ALWAYS:
- If functionality won't work without a parameter, make it a **required positional** parameter.
- Any time you modify a source file, ensure its accompanying test under
  `netbox_wordpress/tests/` contains **comprehensive tests for the change WITHOUT MOCKS**, so
  `manage.py test netbox_wordpress` discovers them, and update any `.md` in the same directory.
- Write concise code (avoid obvious comments; one-liners where possible).
- **SPDX header on every source file**: `# SPDX-License-Identifier: AGPL-3.0-or-later`.

### DO NOT, EVER, UNDER ANY CIRCUMSTANCE:
- Make assumptions, or answer with "is likely", "probably", or "might be".
- Store a WP salt, DB password, or any secret value in a model field. Only OpenBao path refs.
- Re-model the running service, its HA pairing, or the database — those are
  `netbox_services.ServiceInstance` / `netbox_services.HAMirror` / `netbox_database.*`. Compose
  by FK; never duplicate.
- Re-introduce a `config_context` blob or a CustomField/JSONField used as a data-blob.
- Use frame-local / thread-local state instead of passing data via parameters.
- Skip a failing test; keep a broken path as a fallback; or re-implement a function in a second
  place to bypass the original.
- **Mock the database, the ORM, the NetBox API test client, or any integration path.** Tests run
  against a **real test database**; build real `dcim.Device` / `virtualization.VirtualMachine`
  and (where linked) `netbox_services` / `netbox_database` rows.

### Python / Django Guidelines:
- Import children of `datetime`: `from datetime import date` — never `import datetime`.
- Package-relative imports inside `netbox_wordpress` (`from .models import WordPressSite`).
- Cross-plugin/core FKs are declared by **string label** in models
  (`"netbox_services.ServiceInstance"`, `"netbox_database.Database"`, `"dcim.Device"`,
  `"virtualization.VirtualMachine"`); filtersets may import the model classes directly (loaded
  after `required_plugins`).
- Models inherit `netbox.models.NetBoxModel` (custom fields, tags, journaling, GraphQL — free).

---

## Architecture (NetBox 4.6 plugin)

| File | Responsibility |
|------|----------------|
| `__init__.py` | `PluginConfig` — name `netbox_wordpress`, `base_url='wordpress'`, min/max 4.6, `required_plugins` |
| `choices.py` | `PluginSourceChoices`, `WPConstantTypeChoices`, `RelocationStateChoices`, `FPMProfileChoices` |
| `models.py` | the 5 models (see below) + `WordPressSite.clean()` exactly-one-host rule |
| `migrations/0001_initial.py` | hand-authored (NetBox disables makemigrations in prod); verify with `makemigrations --check --dry-run` |
| `api/serializers.py`, `api/views.py`, `api/urls.py` | REST (`NetBoxModelViewSet`) — the contract the tofu-wordpress provider reads |
| `filtersets.py` | `NetBoxModelFilterSet` per model (`search()` + explicit FK-by-PK filters) |
| `tables.py`, `forms.py`, `navigation.py`, `views.py`, `urls.py` | UI (generic NetBox views) |
| `templates/netbox_wordpress/wordpresssite.html` | custom detail page (extends `generic/object.html`): host, DB, tuning, related plugins/themes/content-dir |
| `graphql/__init__.py` | placeholder (auto GraphQL via `NetBoxModel`) |

### Model — WordPress app-config SoT
- **WordPressSite**: `name` (unique); host = exactly one of `device` (`dcim.Device`) /
  `virtual_machine` (`virtualization.VirtualMachine`), enforced by `clean()`; FK
  `service_instance`, `database`, `db_user`; `site_url`, `wp_version`, `table_prefix` (`wp_`),
  `is_multisite`, `fpm_profile` (low/medium/high), `wp_memory_limit`, `prod_hardening`,
  `salt_ref` (OpenBao path). The five composed FKs are `PROTECT`.
  - **WordPressConstant** (FK, CASCADE): `name`, `value`, `value_type`; unique `(site, name)`.
  - **WordPressPlugin** (FK, CASCADE): `slug`, `version` (blank=latest), `is_active`, `source`
    (wporg/url/zip), `source_url`; unique `(site, slug)`.
  - **WordPressTheme** (FK, CASCADE): same shape as plugin; unique `(site, slug)`.
  - **WordPressContentDirectory** (1:1, CASCADE): `content_dir`, `uploads_dir`,
    `target_content_dir`, `content_url`, `relocation_state` (in_place→relocating→relocated). SoT
    for the tofu-wordpress relocation contract (quiesce→move+verify→rewrite defines→symlink/health→rollback).

---

## Testing (NO MOCKS — real DB, NetBox test framework)

- Tests live in `netbox_wordpress/tests/` (`test_models.py`, `test_api.py`, `test_filtersets.py`),
  with real-object builders in `tests/utils.py` (`create_test_vm`, `create_wp_site`). Use
  `utilities.testing` base classes (`APIViewTestCases.*` CRUD mixins, `create_test_device`).
- WordPressSite host-binds per row; WordPressContentDirectory is 1:1 to a site, so API
  `create_data` rows each target a fresh site.
- **Never skip a failing test** — fix the root cause.
- **Run**: `python /opt/netbox/app/netbox/manage.py test netbox_wordpress --keepdb -v2`.
- **Verification owed (cannot run offline — no NetBox env in the build host):**
  `makemigrations netbox_wordpress --check --dry-run` on an ephemeral NetBox, and a full test
  run. Re-confirm the cross-plugin FK targets (`netbox_services.serviceinstance`,
  `netbox_database.database`, `netbox_database.databaseuser`) resolve against the pinned 4.6.
  `py_compile` on all modules is the only static gate available in this build host, and passes.

---

## Licensing
- **AGPL-3.0-or-later** (workspace production-IaC standard). SPDX header in every file.
