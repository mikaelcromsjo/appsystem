# Import Architecture

Strict layered hierarchy — lower layers never import from higher layers.

```
core/models/base.py          # Base = declarative_base()  ← no internal imports
        │
core/models/models.py        # BaseMixin, User, Tag, Update
        │                    # imports: core.models.base
        │
core/database.py             # engine, SessionLocal, get_db, init_admin_user
        │                    # imports: core.models.base (Base)
        │                    # lazy import: core.models.models.User (inside init_admin_user only)
        │
core/functions/helpers.py    # populate, render, build_filters, utc_to_local, formatPhoneNr
        │                    # imports: core.models.base, data.constants, templates
        │
models/*.py                  # domain ORM models + Pydantic schemas (one file per entity)
        │                    # imports: core.models.base (Base), core.models.models (BaseMixin)
        │                    # NEVER import from core.database
        │
models/models.py             # compatibility re-export shim only
        │
functions/*.py               # domain business logic
        │                    # imports: models.*, core.functions.helpers, core.database
        │
scheduler.py                 # alarm background task
middleware.py                # LanguageMiddleware
        │                    # imports: core.i18n, templates
        │
routers/*.py                 # HTTP route handlers
        │                    # imports: models.*, functions.*, core.*, templates
        │
main.py                      # app factory — imports everything, wires it together
```

## Rules

1. `core/models/base.py` — imports nothing from this project
2. `core/models/models.py` — imports only from `core.models.base`
3. `core/database.py` — imports only from `core.models.base`; lazy-import models inside functions
4. Domain `models/*.py` — import `Base` from `core.models.base`, `BaseMixin` from `core.models.models`; never from `core.database`
5. `core/functions/helpers.py` — may import `templates` (needed for `render()`); nothing else from app layer
6. Routers — may import from any layer below them; never from `main.py` or `middleware.py`
7. `main.py` — only file that wires all layers together

## Adding a new entity

1. Create `models/<entity>.py` — imports `Base` from `core.models.base`, `BaseMixin` from `core.models.models`
2. Add re-export line to `models/models.py`
3. Create `routers/<entity>.py` with `APIRouter`
4. Include router in `main.py`
