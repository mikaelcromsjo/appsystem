# TODO — Refactor for AI-extensibility

## Done

- [x] Strip `main.py` to app factory only
- [x] Extract `alarm_scheduler` → `scheduler.py`
- [x] Extract i18n helpers → `core/i18n.py`, `LanguageMiddleware` → `middleware.py`
- [x] Extract auth/root routes → `routers/auth.py`
- [x] Consolidate constants → `core/config.py` (secrets, JWT, DEBUG)
- [x] Secrets read from env vars; `ACCESS_TOKEN_EXPIRE_MINUTES` default → 60
- [x] Split `models/models.py` → one file per entity; shim for compat
- [x] Move `BaseMixin`, `Update` → `models/base.py`
- [x] Move `User`, `UserUpdate` → `models/user.py`
- [x] Move `Tag`, `TagLink` → `models/tag.py`
- [x] `core/models/models.py` → re-export shim
- [x] Split `core/functions/helpers.py` → `datetime_utils`, `phone`, `populate`, `filters`, `render`
- [x] `build_filters` debug `print()` → `logger`
- [x] Fix circular import — `Base` always from `core.models.base`
- [x] `core/database.py` — lazy-import `User`; conditional `connect_args` for SQLite vs Postgres
- [x] `CustomerUpdate.tags` → `List[str]` with Tagify-aware validator
- [x] Jinja2 cache disabled only when `DEBUG=true`
- [x] Delete root-level duplicate JSON files
- [x] Delete `core/inspect_db.py` (duplicate of `scripts/inspect_db.py`)
- [x] Delete orphaned dev files
- [x] Add `docs/IMPORTS.md`, `docs/DOCS.md`

## Remaining (future)

- [ ] `filter_a…filter_h` on `Customer` — replace with `extra` JSON (requires DB migration)
- [ ] `type_a…type_h` on `Product` — same
- [ ] Move `functions/` domain logic closer to routers or merge hierarchy
