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

---

## Structural Issues (bug fixes — do separately)

- [ ] **`alarms.router` included twice** in old `main.py` — fixed in new main.py
- [ ] **Two `@app.exception_handler`** for same type — fixed in new main.py (merged into one)
- [ ] **Hardcoded secrets** — `SESSION_SECRET`, `JWT_SECRET_KEY` still plain strings in `core/config.py`; move to env vars
- [ ] **`connect_args={"check_same_thread": False}`** in `database.py` — SQLite-only arg, breaks Postgres
- [ ] **`ACCESS_TOKEN_EXPIRE_MINUTES = 1`** — likely leftover dev value
- [ ] **`templates.env.cache = {}`** — disables Jinja2 cache globally including production
- [ ] **`CustomerUpdate.tags` typed `Optional[str]`** but `Customer.tags` is JSON column — type mismatch
- [ ] **`core/inspect_db.py` and `scripts/inspect_db.py`** — duplicate file

---

## Remaining Refactor

- [ ] **Consolidate `functions/` and `core/functions/`** — two parallel helper hierarchies; merge into one
- [ ] **Consolidate `models/` and `core/models/`** — `core/models/` holds `BaseMixin`, `User`, `Tag`; consider moving to `models/`
- [ ] **Move JSON config files** — root-level `*.json` duplicates already in `data/`; delete root copies
- [ ] **Replace `filter_a…filter_h` on `Customer`** with `extra` JSON — 8 hardcoded booleans, not extensible
- [ ] **Replace `type_a…type_h` on `Product`** with `extra` JSON — same pattern
- [ ] **`build_filters` debug `print()` calls** in `core/functions/helpers.py` — should use logger
- [ ] **`core/functions/helpers.py` is too large** — split into `populate.py`, `filters.py`, `datetime_utils.py`
