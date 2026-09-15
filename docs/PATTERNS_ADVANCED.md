# Advanced Patterns

**Load: when implementing WebSockets, custom verticals, or polymorphic features**

## 1. Polymorphic tags

```python
# Tag an object
link = TagLink(tag_id=tag.id, object_id=customer.id, object_type="customer")
db.add(link)

# Query tags for an object
links = db.query(TagLink).filter_by(object_id=id, object_type="customer").all()
```

## 2. New vertical checklist

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

## 3. Entity checklist

- [ ] `models/<entity>.py` — ORM + Pydantic schema; `Base` from `core.models.base`, `BaseMixin` from `models.base`
- [ ] Add re-export to `models/models.py`
- [ ] `routers/<entity>.py` — `APIRouter(prefix="/<entity>s")`; use `Update` + `populate()` pattern
- [ ] Include router in `main.py`
- [ ] Templates in `templates/<entity>/` — list, info, edit fragments
- [ ] Alembic migration if DB schema changed
