# Project Structure

```
backend/
  main.py          app factory — middleware + router wiring only
  scheduler.py     alarm background task (asyncio)
  middleware.py    LanguageMiddleware (i18n per request)
  templates.py     Jinja2 loader + filters (todatetime, date, now, timedelta)
  state.py         global dicts: active_connections, user_data (WebSocket)

  core/
    config.py      env-based constants: JWT_SECRET_KEY, SESSION_SECRET,
                   ACCESS_TOKEN_EXPIRE_MINUTES, DEBUG, SUPPORTED_LANGUAGES
    auth.py        get_current_user() — FastAPI dependency
    database.py    engine, SessionLocal, get_db(), init_admin_user()
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
    user.py        User, UserUpdate
    tag.py         Tag, TagLink (polymorphic tagging)
    alarm.py       Alarm
    call.py        Call, CallUpdate
    caller.py      Caller
    company.py     Company, CompanyUpdate
    customer.py    Customer, CustomerUpdate  (tags validator built-in)
    invoice.py     Invoice, InvoiceNumber, InvoiceUpdate
    product.py     Product, ProductUpdate
    product_customer.py  ProductCustomer (M2M junction)
    models.py      re-export shim (backward compat)

  routers/
    auth.py        /login /logout /dashboard /get-ws-token /users/create
    customers.py   /customers/*
    products.py    /products/*
    calls.py       /calls/* + WebSocket /calls/ws  ← see calls.py.md
    alarms.py      /alarms/*
    callers.py     /callers/*
    invoices.py    /invoices/*
    companies.py   /companies/*
    tags.py        /tags/*
    user.py        /user/*
    admin.py       /admin/*

  functions/
    customers.py   get_user_customers(), get_selected_ids(), assign_customers_caller()

  data/
    constants.py   DEFAULT_TZ, load_json(), *_map dicts (loaded at startup)
    *.json         categories, products, organisations, personalities, filters

  scripts/
    manage_users.py    CLI: create/update users
    inspect_db.py      CLI: inspect model schema and rows
    generate_stats.py  stats generation
    generate_test_data.py  seed test data

  templates/
    base.html      full page shell (nav + content container)
    base_mobile.html
    login.html
    <domain>/      HTMX fragments per domain

  alembic/         DB migrations
```

## Env vars

| Var | Default | Notes |
|-----|---------|-------|
| `DATABASE_URL` | required | e.g. `sqlite:////dbdata/app.db` |
| `DEBUG` | `false` | disables Jinja cache, enables hot reload |
| `JWT_SECRET_KEY` | `supersecret-jwt-key` | change in production |
| `SESSION_SECRET` | `super-secret-key` | change in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | WS token lifetime |
