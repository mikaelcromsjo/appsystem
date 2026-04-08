# TODO — Refactor for AI-extensibility

## Domains

- **Core**: `core/` — auth, db, base models, lang, helpers, static
- **Domain Models**: `models/` — one file per entity (ORM + Pydantic)
- **Routers**: `routers/` — HTTP endpoints per domain
- **Functions**: `functions/` — domain business logic
- **Data**: `data/` — constants, JSON config
- **Templates**: `templates/` — Jinja2 HTML fragments
- **Scripts**: `scripts/` — CLI admin tools
- **State**: `state.py` — global WebSocket connections

---

## Done

- [x] Extract `alarm_scheduler` → `scheduler.py`
- [x] Extract i18n helpers → `core/i18n.py`
- [x] Extract `LanguageMiddleware` → `middleware.py`
- [x] Extract auth/root routes → `routers/auth.py`
- [x] Move JWT/session constants → `core/config.py` (removes duplicate in `routers/calls.py`)
- [x] Move Jinja filter setup (`todatetime`, `now`, `timedelta`) → `templates.py`
- [x] Strip `main.py` to app factory only
- [x] Split `models/models.py` into one file per entity
- [x] Keep `models/models.py` as compatibility re-export shim
- [x] Fix circular import — `Base` always from `core.models.base`; `core/database.py` lazy-imports `User`
- [x] Add `docs/IMPORTS.md` — layered import architecture

---

## Phase 1 — Refactor (structural, no behavior change)

### 1. Split `core/functions/helpers.py`
Too large; mixed concerns. Split into:
- `core/functions/datetime_utils.py` — `local_to_utc`, `utc_to_local`
- `core/functions/phone.py` — `formatPhoneNr`
- `core/functions/populate.py` — `populate`, `convert_value_for_field`, `_convert_value`
- `core/functions/filters.py` — `build_filters`
- `core/functions/render.py` — `render`
Keep `core/functions/helpers.py` as re-export shim (same as `models/models.py` pattern).

### 2. Consolidate `core/models/` into `models/`
`core/models/` currently holds `BaseMixin`, `User`, `Tag`, `TagLink`, `Update`.
These are domain models — they belong in `models/`.
- Move `BaseMixin`, `Update` → `models/base.py`
- Move `User`, `UserUpdate` → `models/user.py`
- Move `Tag`, `TagLink` → `models/tag.py`
- Keep `core/models/base.py` (just `Base = declarative_base()`) — stays in `core/` since database.py depends on it
- Keep `core/models/models.py` as re-export shim until all imports are updated
- Update `core/auth.py` and `core/database.py` to import from new locations

### 3. Move root-level JSON config files → `data/` only
`backend/*.json` files are duplicates of `backend/data/*.json`.
Delete: `backend/categories.json`, `backend/filters.json`, `backend/organisations.json`,
`backend/personalities.json`, `backend/products.json`.

---

## Phase 2 — Logical Updates

### 4. Move secrets to env vars
`core/config.py` — `SESSION_SECRET` and `JWT_SECRET_KEY` are plain strings.
Read from `os.environ` with a fallback warning in dev only.
No code structure change, just config wiring.

### 5. Fix `CustomerUpdate.tags` type mismatch
`CustomerUpdate.tags` is `Optional[str]` but `Customer.tags` is a JSON column.
Change `CustomerUpdate.tags` to `Optional[List[str]]` and update the `populate()` call
in the customers router to handle the list correctly.

### 6. Replace `print()` with `logger` in `build_filters`
`core/functions/helpers.py` (→ `filters.py` after step 1) has ~15 debug `print()` calls.
Replace with `logger.debug()` so they're silenced in production.

### 7. Fix `templates.env.cache` in production
`templates.env.cache = {}` disables caching always.
Gate on a `DEBUG` flag from config: only disable in dev.

---

## Phase 3 — Bug Fixes

### 8. Fix `connect_args` for Postgres
`core/database.py` — `connect_args={"check_same_thread": False}` is SQLite-only.
Only apply it when `DATABASE_URL` starts with `sqlite`.

### 9. Fix `ACCESS_TOKEN_EXPIRE_MINUTES`
Value is `1` (one minute) — likely a dev leftover.
Set to a sensible default (e.g. `60`) or read from env.

---

## Phase 4 — Remove Unused Files

### 10. Delete duplicate `inspect_db.py`
`core/inspect_db.py` and `scripts/inspect_db.py` — keep only `scripts/inspect_db.py`.

### 11. Delete pre-existing orphan files (already removed from working tree)
These were deleted locally but never committed. Stage and commit their removal:
`Dockerfile - Copy`, `_docker-compose.override.yml`, `add db version.txt`,
`added in total`, `commands.txt`, `commitslog.csv`, `docker info.txt`,
`git-pull.sh`, `git-push-dev.bat`, `git-push.bat`, `save snippets.txt`,
`certs/localhost-key.pem`, `certs/localhost.pem`
