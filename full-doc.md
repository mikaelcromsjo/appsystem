# Patterns

## 1. CRUD Upsert (create or update)

```python
@router.post("/entity/upsert")
async def upsert_entity(request: Request, update_data: Update,
                        db: Session = Depends(get_db), user=Depends(get_current_user)):
    id = update_data.model_dump().get("id")
    record = db.query(Entity).filter(Entity.id == int(id)).first() if id else Entity()

    data_dict = update_data.model_dump()

    # Move extra.* keys into the extra dict
    for key in [k for k in data_dict if k.startswith("extra.")]:
        data_dict.setdefault("extra", {})[key.split(".", 1)[1]] = data_dict.pop(key)

    # Pop FK relationships before populate, handle after
    related_id = data_dict.pop("related_id", None)

    record = populate(data_dict, record, EntityUpdate)

    if related_id:
        record.related = db.get(Related, int(related_id))

    db.add(record)
    db.commit()
    return render("entity/info.html", {"request": request, "entity": record})
```

## 2. HTMX render

```python
from core.functions.render import render

# Returns fragment if hx-request header present, full page otherwise
return render("customers/list.html", {"request": request, "customers": customers})
```

`base.html` renders the full shell + loads `content_template` into the content div.
Direct navigation gets the full page; HTMX swaps only the fragment.

## 3. HTMX response headers

```python
response = HTMLResponse("")
response.headers["HX-Trigger"] = "customersReload"   # fire JS event
response.headers["HX-Popup-Message"] = "Saved"       # show toast
response.headers["HX-Redirect"] = "/customers/"      # redirect
```

## 4. Filter session pattern

```python
# Store filters in session
request.session["customer_filters"] = dict(await request.form())

# Read + apply
filter_dict = request.session.get("customer_filters", {})
filters = build_filters(filter_dict, Customer)
sql_filters = [f for f in filters if not isinstance(f, dict)]
query = query.filter(*sql_filters)
```

`build_filters` returns SQLAlchemy filter objects + `{"exact_vals": [...], "column": "..."}` dicts for Python-side exact matching. See `filters.py.md`.

## 5. WebSocket flow

```
Client → GET /get-ws-token → short-lived JWT
Client → WS /calls/ws?token=<jwt>
Server → validates JWT → stores websocket in active_connections[user_id]
scheduler.py → queries due alarms → sends JSON payload to active connections
```

## 6. BaseMixin.empty()

```python
# Create an unsaved instance with type-inferred empty values
customer = Customer.empty(user_id="1", team_id=2)
# Useful for pre-populating create forms
return render("customers/edit.html", {"request": request, "customer": customer})
```

Override defaults per model with `__empty_overrides__ = {"field": value}`.

## 7. Polymorphic tags

```python
# Tag an object
link = TagLink(tag_id=tag.id, object_id=customer.id, object_type="customer")
db.add(link)

# Query tags for an object
links = db.query(TagLink).filter_by(object_id=id, object_type="customer").all()
```

## 8. Adding a new vertical

1. Create `backend/verticals/<slug>/__init__.py` with the manifest:
   ```python
   slug = "tickets"
   label = "Tickets"
   order = 60          # controls nav position
   admin_only = False

   hx_endpoint = "tickets_list"    # FastAPI route name
   content_div_id = "tickets_content"

   def get_routers():
       from routers import tickets
       return [tickets.router]
   ```
2. Create `backend/routers/tickets.py` with `router = APIRouter(prefix="/tickets")` and a named `tickets_list` route.
3. Templates go in `backend/templates/tickets/` as normal.
4. Restart — `core/loader.py` discovers the vertical automatically; nav and content divs appear.
5. To limit which verticals run: `ENABLED_VERTICALS=customers,calls,tickets`.

No changes to `main.py` or `base.html` needed.

## 9. Multi-tenant auth flow

```
POST /login (email + password)
  → verify GlobalUser in master DB
  → if one tenant: store tenant_db_url in session, redirect to dashboard
  → if many tenants: store global_user_id in session, redirect to /pick-tenant
  → if require_2fa: send LoginToken email, redirect to /verify-pending

GET /pick-tenant  →  POST /pick-tenant
  → store tenant_db_url in session, send 2FA email if require_2fa

GET /verify-email?token=<uuid>
  → look up LoginToken in master DB (expires 15 min, single-use)
  → set tenant_db_url in session, clear token, redirect to dashboard
```

Session keys set by auth:
- `tenant_db_url` — resolved tenant DB URL; required by `get_db()`
- `global_user_id` — temporary, used before tenant is selected

`get_db(request)` raises HTTP 401 if `tenant_db_url` is absent.  
Use `get_master_db()` for routes that touch GlobalUser / Tenant / LoginToken.

## 10. Rows/reload pattern

Lists are split into two endpoints: a shell (`list.html`) and rows-only fragment (`rows.html`).  
Filters and upserts fire `HX-Trigger` events; the rows div listens and reloads itself.

```python
# Shell endpoint — renders full list page once
@router.get("/", name="customers_list")
def customers_list(...):
    return templates.TemplateResponse("customers/list.html", {...})

# Rows endpoint — reloaded on events
@router.get("/rows", name="customers_rows")
def customers_rows(...):
    customers = get_user_customers(db, request, user)
    return templates.TemplateResponse("customers/rows.html", {"request": request, "customers": customers})

# Filter/upsert — fire event instead of re-rendering
response = HTMLResponse("")
response.headers["HX-Trigger"] = "customersRowsReload"
return response
```

In `list.html`, the rows div listens:
```html
<div hx-get="/customers/rows" hx-trigger="load, customersRowsReload from:body" hx-target="this">
```

Event naming convention: `<slug>RowsReload` (e.g. `alarmsRowsReload`, `invoicesRowsReload`).

## 9. Adding a new entity (checklist)

- [ ] `models/<entity>.py` — ORM + Pydantic schema; `Base` from `core.models.base`, `BaseMixin` from `models.base`
- [ ] Add re-export to `models/models.py`
- [ ] `routers/<entity>.py` — `APIRouter(prefix="/<entity>s")`; use `Update` + `populate()` pattern
- [ ] Include router in `main.py`
- [ ] Templates in `templates/<entity>/` — list, info, edit fragments
- [ ] Alembic migration if DB schema changed
# Project Structure

```
backend/
  main.py          app factory — middleware + router wiring only
  scheduler.py     alarm background task (asyncio)
  middleware.py    LanguageMiddleware (i18n per request)
  templates.py     Jinja2 loader + filters (todatetime, date, now, timedelta)
  state.py         global dicts: active_connections, user_data (WebSocket)

  core/
    loader.py      discover(), get_routers(), get_nav_items() — reads verticals/
    config.py      env-based constants: JWT_SECRET_KEY, SESSION_SECRET,
                   ACCESS_TOKEN_EXPIRE_MINUTES, DEBUG, SUPPORTED_LANGUAGES,
                   SMTP_*, ADMIN_EMAIL, ADMIN_PASSWORD, APP_BASE_URL
    auth.py        get_current_user() — FastAPI dependency; auto-assigns "Admin" team if user.team_id is None
    database.py    multi-tenant engines; get_db() (tenant), get_master_db(),
                   init_admin_user(), _get_tenant_engine() cache
    email.py       send_login_link() — SMTP 2FA email
    i18n.py        get_translator_cached(), get_best_language_match()
    lang.py        translation loader
    lang/
      lang_sv.json Swedish translations
    models/
      base.py      Base = declarative_base()  ← no deps
      models.py    re-export shim → models/
    functions/
      datetime_utils.py  local_to_utc, utc_to_local
      phone.py           formatPhoneNr
      populate.py        populate(), convert_value_for_field()  ← see populate.py.md
      filters.py         build_filters()                        ← see filters.py.md
      render.py          render() — HTMX-aware template response
      helpers.py         re-export shim (backward compat)
    static/        css, js, images (served at /static)

  models/
    base.py        BaseMixin (.empty(), .to_dict()), Update (Pydantic)
    master.py      MasterBase + GlobalUser, Tenant, UserTenant, LoginToken
                   (master DB only — never imported by tenant models)
    user.py        User, UserUpdate  (global_user_id links to GlobalUser)
    account.py     Account, AccountUpdate
    tag.py         Tag, TagLink (polymorphic tagging)
    alarm.py       Alarm
    call.py        Call, CallUpdate
    team.py        Team  (table: teams; has account_id FK)
    company.py     Company, CompanyUpdate
    customer.py    Customer, CustomerUpdate  (tags validator built-in)
    invoice.py     Invoice, InvoiceNumber, InvoiceUpdate  (team_id FK → Team)
    product.py     Product, ProductUpdate
    product_customer.py  ProductCustomer (M2M junction)
    models.py      re-export shim (backward compat)

  routers/
    auth.py        /login /logout /pick-tenant /verify-email /dashboard
                   /get-ws-token /users/create
    customers.py   /customers/*
    products.py    /products/*
    calls.py       /calls/* + WebSocket /calls/ws  ← see calls.py.md
    alarms.py      /alarms/*
    teams.py     /teams/*
    invoices.py    /invoices/*
    companies.py   /companies/*
    tags.py        /tags/*
    user.py        /user/*
    admin.py       /admin/* — includes POST /users/create-team, POST /users/{id}/update-team

  functions/
    customers.py   get_user_customers(), get_selected_ids(), assign_customers_team()

  data/
    constants.py   DEFAULT_TZ, load_json(), *_map dicts (loaded at startup)
    *.json         categories, products, organisations, personalities, filters

  verticals/              plugin vertical packages — each is self-contained
    <slug>/
      __init__.py         manifest: slug, label, order, admin_only,
                          hx_endpoint, content_div_id, get_routers()
    customers/  products/  calls/  alarms/  invoices/  admin/

  scripts/
    manage_users.py    CLI: create/update users
    create_tenant.py   CLI: provision new tenant (master DB + tenant DB + admin user)
    inspect_db.py      CLI: inspect model schema and rows
    generate_stats.py  stats generation

  templates/
    base.html           full page shell (nav + content container)
    base_mobile.html
    login.html          email+password form
    pick_tenant.html    tenant selector (shown when user has multiple tenants)
    verify_pending.html waiting page shown after 2FA email is sent
    <domain>/           HTMX fragments per domain

  alembic/         DB migrations
```

## Env vars

| Var | Default | Notes |
|-----|---------|-------|
| `DATABASE_URL` | required | default tenant DB, e.g. `sqlite:////dbdata/app.db` |
| `MASTER_DATABASE_URL` | `DATABASE_URL` | master DB (GlobalUser, Tenant, LoginToken) |
| `DEBUG` | `false` | disables Jinja cache, enables hot reload |
| `JWT_SECRET_KEY` | `supersecret-jwt-key` | change in production |
| `SESSION_SECRET` | `super-secret-key` | change in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | WS token lifetime |
| `ADMIN_EMAIL` | `admin@localhost` | seeded on first start |
| `ADMIN_PASSWORD` | `1234` | seeded on first start |
| `APP_BASE_URL` | `http://localhost:8010` | used in 2FA email links |
| `SMTP_HOST` | `""` | leave empty to disable email |
| `SMTP_PORT` | `587` | |
| `SMTP_USER` | `""` | |
| `SMTP_PASSWORD` | `""` | |
| `SMTP_FROM` | `ADMIN_EMAIL` | sender address |
| `ENABLED_VERTICALS` | _(all)_ | comma-separated slugs to load, e.g. `customers,calls,admin` |
# Data Models

## Master DB (multi-tenancy layer)

```
GlobalUser ──< UserTenant >── Tenant
GlobalUser ──< LoginToken
```

| Model | Table | Notes |
|-------|-------|-------|
| `GlobalUser` | global_users | login identity (email + password), shared across tenants |
| `Tenant` | tenants | per-tenant slug, db_url, require_2fa flag |
| `UserTenant` | user_tenants | M2M: GlobalUser ↔ Tenant |
| `LoginToken` | login_tokens | one-time 2FA token; consumed on first use |

These live in `MASTER_DATABASE_URL`. Never import from tenant models into `master.py`.

## Tenant DB (per-tenant data)

```
Account ──< Team ──< Customer ──< Call
                              └─< Alarm
                              └─< ProductCustomer >─ Product
                              └─< Invoice (via Company)

User >── Team (optional, links local user to a team/agent identity)
User.global_user_id → GlobalUser.id  (no FK across DBs; soft reference)

Tag ──< TagLink (polymorphic: object_id + object_type string)
```

## Entity Summary

| Model | Table | Key relations |
|-------|-------|---------------|
| `Account` | accounts | groups Teams |
| `Team` | teams | belongs to Account; has many Customers |
| `Customer` | customers | belongs to Team; has Calls, Alarms, ProductCustomers |
| `Call` | calls | belongs to Customer + Team |
| `Alarm` | alarms | belongs to Customer + Team; optional Product |
| `Product` | products | has many ProductCustomers |
| `ProductCustomer` | product_customers | M2M: Customer ↔ Product, with status |
| `Company` | companies | has many Invoices |
| `Invoice` | invoices | belongs to Company; optional Team (team_id) |
| `User` | users | optional Team link; `global_user_id` soft-refs GlobalUser |
| `Tag` | tags | linked via TagLink |
| `TagLink` | tag_links | polymorphic: (object_id, object_type) |

## Key field conventions

- `extra` — `MutableDict JSON` on every model; use for extensible fields without migrations
- `status` — `Integer` on Call (call outcome) and ProductCustomer (attendance state)
- `team_id` — FK on Customer, Call, Alarm, User, Invoice pointing to `teams` (Team) table
- `global_user_id` — on User; soft cross-DB reference to `master.global_users.id`
- `filter_a…filter_h` — 8 boolean columns on Customer (legacy; prefer `extra` for new fields)
- `type_a…type_h` — 8 boolean columns on Product (legacy; prefer `extra` for new fields)

## ProductCustomer status values

`0` no input · `1` not going · `2` maybe · `3` going · `4` paid · `5` attended
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
# Documentation Index

## Always load
- [PATTERNS.md](PATTERNS.md) — CRUD, HTMX render, filters, WebSocket, entity checklist
- [STRUCTURE.md](STRUCTURE.md) — full directory map + env vars

## Load when relevant
- [MODELS.md](MODELS.md) — entity relationships, field conventions
- [IMPORTS.md](IMPORTS.md) — import layer rules, adding new entities

## Reports & planning
- [REPORT_MODULARITY.md](REPORT_MODULARITY.md) — multi-vertical SaaS modularity, AI codegen, missing infrastructure
- [PLAN_customer_extra_migration.md](PLAN_customer_extra_migration.md) — move code_name, controlled, filter_a–h from columns into customer.extra JSON (5 staged steps)

## Per-file (complex files only)
- [populate.py.md](../backend/core/functions/populate.py.md)
- [filters.py.md](../backend/core/functions/filters.py.md)
- [calls.py.md](../backend/routers/calls.py.md)
