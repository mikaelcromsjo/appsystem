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
customer = Customer.empty(user_id="1", caller_id=2)
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

## 9. Adding a new entity (checklist)

- [ ] `models/<entity>.py` — ORM + Pydantic schema; `Base` from `core.models.base`, `BaseMixin` from `models.base`
- [ ] Add re-export to `models/models.py`
- [ ] `routers/<entity>.py` — `APIRouter(prefix="/<entity>s")`; use `Update` + `populate()` pattern
- [ ] Include router in `main.py`
- [ ] Templates in `templates/<entity>/` — list, info, edit fragments
- [ ] Alembic migration if DB schema changed
