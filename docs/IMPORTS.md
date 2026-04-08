# Import Architecture

Strict layered hierarchy — lower layers never import from higher layers.

```
core/models/base.py        # Base = declarative_base()  ← no deps
        │
models/base.py             # BaseMixin, Update           ← no internal deps
models/user.py             # User, UserUpdate            ← core.models.base, models.base
models/tag.py              # Tag, TagLink                ← core.models.base
        │
core/models/models.py      # re-export shim → models/base, models/user, models/tag
        │
core/database.py           # engine, SessionLocal, get_db, init_admin_user
        │                  # imports: core.models.base
        │                  # lazy: core.models.models.User (inside init_admin_user only)
        │
core/functions/
  datetime_utils.py        # local_to_utc, utc_to_local
  phone.py                 # formatPhoneNr
  populate.py              # populate, convert_value_for_field
  filters.py               # build_filters
  render.py                # render  ← imports templates
  helpers.py               # re-export shim (backward compat)
        │
models/<entity>.py         # ORM + Pydantic per entity
        │                  # imports: core.models.base, models.base
        │                  # NEVER import from core.database
models/models.py           # re-export shim (backward compat)
        │
functions/<domain>.py      # domain business logic
        │
scheduler.py               # alarm background task
middleware.py              # LanguageMiddleware  ← core.i18n, templates
        │
routers/*.py               # HTTP handlers
        │
main.py                    # app factory — wires everything
```

## Rules

1. `core/models/base.py` and `models/base.py` — no internal imports
2. `core/database.py` — only imports `core.models.base`; lazy-import models inside functions
3. Domain `models/*.py` — import `Base` from `core.models.base`, `BaseMixin` from `models.base`; never from `core.database`
4. `core/functions/render.py` — only function file that may import `templates`
5. Routers — may import any layer below; never `main.py` or `middleware.py`
6. `main.py` — only file that wires all layers together

## Adding a new entity

1. `models/<entity>.py` — `Base` from `core.models.base`, `BaseMixin` from `models.base`
2. Add re-export to `models/models.py`
3. `routers/<entity>.py` with `APIRouter`
4. Include router in `main.py`
