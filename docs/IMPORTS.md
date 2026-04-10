# Import Architecture

Strict layered hierarchy — lower layers never import from higher layers.

```
core/models/base.py        # Base = declarative_base()  ← no deps
        │
models/base.py             # BaseMixin, Update           ← no internal deps
models/master.py           # MasterBase + GlobalUser, Tenant, UserTenant, LoginToken
        │                  # imports: models.user (pwd_context only); never core.database
models/user.py             # User, UserUpdate            ← core.models.base, models.base
models/account.py          # Account, AccountUpdate      ← core.models.base, models.base
models/tag.py              # Tag, TagLink                ← core.models.base
        │
core/models/models.py      # re-export shim → models/base, models/user, models/tag
        │
core/database.py           # engines: engine (tenant default), master_engine
        │                  # sessions: SessionLocal, MasterSession
        │                  # deps: get_db(request) (tenant-aware), get_master_db()
        │                  # imports: core.models.base, core.config
        │                  # lazy: core.models.models.User, models.master.*, models.team
        │
core/email.py              # send_login_link()  ← core.config (SMTP vars)
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
        │                  # auth.py also imports models.master, core.email
main.py                    # app factory — wires everything
```

## Rules

1. `core/models/base.py` and `models/base.py` — no internal imports
2. `core/database.py` — only imports `core.models.base` and `core.config` at module level; lazy-import models inside functions
3. `models/master.py` — uses its own `MasterBase`; may import `pwd_context` from `models.user`; never imported by other models
4. Domain `models/*.py` — import `Base` from `core.models.base`, `BaseMixin` from `models.base`; never from `core.database`
5. `core/functions/render.py` — only function file that may import `templates`
6. Routers — may import any layer below; never `main.py` or `middleware.py`
7. `main.py` — only file that wires all layers together

## Tenant-aware get_db

`get_db(request)` reads `request.session["tenant_db_url"]` to route to the correct tenant DB. Routers that need the master DB use `get_master_db()` instead.

## Adding a new entity

1. `models/<entity>.py` — `Base` from `core.models.base`, `BaseMixin` from `models.base`
2. Add re-export to `models/models.py`
3. `routers/<entity>.py` with `APIRouter`
4. Include router in `main.py`
