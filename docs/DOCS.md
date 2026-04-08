# Documentation Index

## Architecture
- [IMPORTS.md](IMPORTS.md) — layered import rules, entity creation guide
- [TODO.md](TODO.md) — refactor backlog and completed work

## Structure
```
backend/
  main.py          app factory, middleware, router wiring
  scheduler.py     alarm background task
  middleware.py    LanguageMiddleware
  templates.py     Jinja2 loader + filters
  state.py         global WebSocket connection store
  core/
    config.py      env-based constants (secrets, flags)
    auth.py        get_current_user dependency
    database.py    engine, SessionLocal, get_db, init_admin_user
    i18n.py        translator cache, language matching
    models/
      base.py      Base = declarative_base()
      models.py    re-export shim → models/
    functions/
      datetime_utils.py  utc/local conversion
      phone.py           phone number formatting
      populate.py        form dict → ORM model
      filters.py         SQLAlchemy filter builder
      render.py          HTMX-aware template renderer
      helpers.py         re-export shim (compat)
  models/
    base.py        BaseMixin, Update
    user.py        User, UserUpdate
    tag.py         Tag, TagLink
    alarm.py       Alarm
    call.py        Call, CallUpdate
    caller.py      Caller
    company.py     Company, CompanyUpdate
    customer.py    Customer, CustomerUpdate
    invoice.py     Invoice, InvoiceNumber, InvoiceUpdate
    product.py     Product, ProductUpdate
    product_customer.py  ProductCustomer
    models.py      re-export shim (compat)
  routers/
    auth.py        login, logout, dashboard, ws-token
    customers/products/calls/alarms/...
  functions/
    customers.py   customer query helpers
  data/
    constants.py   app-wide constants (DEFAULT_TZ etc.)
    *.json         reference data (categories, filters, orgs...)
  scripts/
    manage_users.py   CLI user management
    inspect_db.py     CLI DB inspection
    generate_*.py     test/stats data generators
```
