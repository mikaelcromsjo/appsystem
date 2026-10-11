# Architecture

FastAPI serves Jinja fragments; HTMX swaps them into a single-page tab shell; Alpine
holds client state. One master DB (logins, tenants) plus one DB per tenant.

## Where code goes

| Thing | Location |
|---|---|
| Business module ("vertical") | `backend/verticals/<slug>/` — manifest `__init__.py`, `router.py`, optional `roles.py`, `templates/<slug>/*.html` |
| Infrastructure routes (login, user profile, tags) | `backend/routers/` — wired by hand in `main.py` |
| ORM + Pydantic per entity | `backend/models/<entity>.py` |
| Shared helpers | `backend/core/functions/` |
| Shell, login, shared components | `backend/templates/` |

## Vertical contract

`core/loader.py` imports every package in `backend/verticals/` (not starting with `_`)
and reads these module attributes: `slug`, `label`, `order`, `hx_endpoint` (route
**name** of the tab's entry view), `content_div_id`, `get_routers()`; optional
`admin_only`, `superadmin_only`, `role_defs`, and by convention `COLUMNS` for the list.

- Adding a vertical needs no change to `main.py` or `base.html`: nav button, content
  div and modal are generated from the manifest. A restart is required.
- `content_div_id` is not derived from the slug and is inconsistent
  (`customer_content`, `companies_content`, …). Read it from the manifest.
- Templates are resolved vertical dirs first, then `backend/templates/`. Template
  names are global, hence the `templates/<slug>/` sub-folder.
- A new model must also be imported in `main.py` **and** in `_complete_login()`
  (`routers/auth.py`), or its table is not created.

## Legacy and dead code — do not copy from these

- `backend/routers/customers.py` is not mounted (the live one is
  `verticals/customers/router.py`). `routers/teams.py` is mounted, by the calls vertical.
- Re-export shims still used by most imports: `models/models.py`,
  `core/models/models.py`, `core/functions/helpers.py`. New code should import from
  the real module (`models.customer`, `core.functions.populate`, …).
- `backend/alembic/` and `scripts/migrate_all_tenants.py` are unused leftovers; see below.
- `backend/dev.db`, `backend/stats/output.html`, `backend/core/static/output.html`
  are tracked artefacts, not source.

## Import rules

- `models/*.py` never import `core.database`. `core/database.py` imports models
  lazily inside functions.
- `models/master.py` has its own `MasterBase`; tenant models must not reference it
  (cross-DB links are plain integers, e.g. `User.global_user_id`).
- Only `core/functions/render.py` and routers import `templates`.

## Schema policy

No migrations. Tables are created with `create_all()` — for the default tenant at
startup, for other tenants at each login. `create_all()` never alters an existing
table, so a new column on an existing model needs a recreated database (demo data:
reseed, see `docs/TEST_DATA.md`) or a hand-written `ALTER` like
`_migrate_master_schema()` in `core/database.py`. Prefer a key in the model's
`extra` JSON column when a real column is not needed.

## Background work

`scheduler.py` runs one asyncio loop per process, started at startup. It reads only
the default tenant DB and pushes alarms over the websockets held in `state.py`
(in-memory, per process — a second worker would not see them).
