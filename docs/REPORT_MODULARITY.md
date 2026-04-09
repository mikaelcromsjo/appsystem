# Modularity & AI-Generation Report

> Goal: use one codebase to ship multiple SaaS verticals (call center, invoicing, …)
> without the codebase becoming a tangled monolith that AI can't reliably extend.

---

## 1. Current state — what already works well

| Strength | Why it helps AI generation |
|---|---|
| FastAPI + HTMX fragment pattern | AI can write a complete feature in one file per domain |
| `populate()` + `BaseMixin` | Upsert logic is already abstracted; AI doesn't need to repeat it |
| `render()` with HTMX detection | One return statement works for full pages and fragments |
| `extra` JSON column | AI can add fields without writing migrations |
| Multi-tenant master DB | Clean separation between identity layer and product data |
| Per-file `.py.md` docs | AI can load targeted context without reading full source |

---

## 2. The main modularity problem

Every vertical (calls, invoices, …) is wired directly into `main.py` and shares the same
template folder. Adding a new SaaS application currently means:

- Adding routers to `main.py` manually
- Adding templates into a flat `templates/` tree
- Adding models that all live in the same SQLAlchemy metadata (`Base`)
- No way to "turn off" a vertical per tenant

This makes it impossible to run the call-center vertical for tenant A and the invoicing
vertical for tenant B using the same deployed image.

---

## 3. Ideas — making the system more modular

### 3.1 Plugin-style verticals

Group everything for one vertical into a self-contained directory:

```
verticals/
  calls/
    router.py          # APIRouter with prefix
    models.py          # ORM models (use shared Base)
    templates/         # HTMX fragments
    vertical.py        # metadata: name, slug, nav items, migrations
  invoices/
    ...
  crm/
    ...
```

`main.py` discovers and loads verticals at startup:

```python
for v in settings.ENABLED_VERTICALS:
    mod = importlib.import_module(f"verticals.{v}.vertical")
    app.include_router(mod.router)
```

`ENABLED_VERTICALS` is set per tenant in `Tenant.config` (JSON column).  
Result: one Docker image, many SaaS products.

**AI impact:** AI gets a clear, bounded scope. "Add a vertical called `tickets`" maps
to a single directory with a fixed file structure — no global rewiring needed.

---

### 3.2 Vertical manifest (`vertical.py`)

Each vertical exports a small manifest:

```python
# verticals/calls/vertical.py
name = "Call Center"
slug = "calls"
router = router            # FastAPI APIRouter
nav = [{"label": "Calls", "url": "/calls/", "icon": "phone"}]
models = [Call, Alarm]     # for create_all / Alembic discovery
```

`base.html` reads `nav` from loaded verticals to build the sidebar dynamically.  
No more hardcoded nav links.

---

### 3.3 Replace `filter_a…filter_h` with typed `extra` fields

The 8 boolean filter columns on `Customer` are a prototype relic. Replace with:

```python
extra = {"tags": [...], "type": "premium", "segment": "B2B"}
```

Add a GIN index (Postgres) or JSON extract index (SQLite) so filters stay fast.
AI can define new filter fields purely in the template + router — no migration.

---

### 3.4 Schema-driven list pages

Instead of hardcoding `<th>` columns in every list template, define columns in the
vertical manifest or router:

```python
COLUMNS = [
    {"key": "name",       "label": "Name",   "sortable": True},
    {"key": "status",     "label": "Status", "sortable": True},
    {"key": "created_at", "label": "Created", "sortable": True},
]
```

Pass `COLUMNS` to a generic `list.html` base template.  
AI can add a new column by adding one dict — no template surgery.

---

### 3.5 Shared component library (`templates/components/`)

Extract repeating HTMX patterns into reusable Jinja2 macros:

```
templates/components/
  table.html       # generic sortable/filterable table
  modal.html       # slide-in edit panel
  filter_bar.html  # filter form with session persistence
  toast.html       # HX-Popup-Message handler
  confirm.html     # delete confirmation dialog
```

AI-generated features import macros instead of reinventing structure each time.
Reduces per-feature template size by ~60%.

---

### 3.6 AI-optimized code generation hints

Add a `CODEGEN.md` alongside each vertical that tells AI exactly what to do:

```markdown
# CODEGEN — calls vertical

## Add a new field to Call
1. Add column to `models.py` + `CallUpdate`
2. Add field to `templates/calls/edit.html`
3. Done — populate() handles the rest

## Add a new list filter
1. Add filter option to `templates/calls/filter.html`
2. Map field in `routers/calls.py` → build_filters()
```

Short, imperative, no background. Makes AI generations more reliable because the
agent always knows the minimum surface area to touch.

---

## 4. Missing general SaaS infrastructure — what to build next

### Priority 1 — Tenant configuration UI
Tenants currently have no self-service settings page. Needed:
- Enabled verticals toggle per tenant
- SMTP override per tenant
- 2FA on/off per tenant
- Branding (logo, primary color)

### Priority 2 — Billing / subscription tracking
Even a simple model goes a long way:
- `Subscription(tenant_id, plan, status, trial_ends_at, seats)`
- Gate features by plan in `get_current_user()`
- Webhook receiver for Stripe events

### Priority 3 — Audit log
Critical for any B2B SaaS:
- `AuditEvent(tenant_id, user_id, action, object_type, object_id, diff, ts)`
- Write on every upsert/delete via a FastAPI middleware or `populate()` hook
- Simple read-only UI in admin panel

### Priority 4 — Role-based access (RBAC)
Currently binary: `user.admin` flag. Needed:
- `Role(name, permissions: JSON list)`
- `UserRole(user_id, role_id)`
- Permission check decorator: `@require_permission("customers.write")`
- Per-vertical permission namespaces

### Priority 5 — Notification center
- `Notification(user_id, type, payload, read_at)`
- WebSocket push (infrastructure already exists via `active_connections`)
- In-app bell icon + HTMX-polled badge count

### Priority 6 — File/attachment storage
- `Attachment(object_type, object_id, filename, storage_key, content_type, size)`
- Pluggable backend: local filesystem (dev) → S3-compatible (prod)
- Generic upload endpoint; vertical templates drop in an upload button

### Priority 7 — CSV / Excel import + export
- Most B2B customers want bulk import
- Generic importer: column mapping UI → `populate()` loop → error report
- Generic exporter: query → `openpyxl` or `csv.writer` streaming response

### Priority 8 — Public API + API keys
- `ApiKey(tenant_id, user_id, key_hash, scopes, last_used_at)`
- Thin FastAPI router mirroring existing CRUD endpoints
- Enables external integrations without building a separate service

---

## 5. AI code generation — practical guidelines

### What works well now
- Asking AI to add a single vertical or endpoint works reliably because each router
  is self-contained.
- `populate()` means AI never needs to write field-assignment loops.
- `render()` means AI never needs to think about full-page vs fragment.

### What breaks AI generation today
- Global `models.py` re-export shim becomes a coordination point — AI forgets to
  add entries.
- Hardcoded nav in `base.html` means AI needs to touch a shared file for every
  new vertical.
- No codegen docs per vertical — AI reads the whole codebase and produces
  inconsistent results.

### Recommended workflow (human + AI)
1. Human: define vertical manifest + column schema
2. AI: scaffold router, models, templates from manifest
3. Human: review; AI fills in business logic per endpoint
4. Human: run Alembic migration if needed
5. AI: write per-file `.py.md` doc for any complex file

This keeps AI in bounded, verifiable increments and the human at decision points.

---

## 6. Summary — recommended sequence

| Step | What | Payoff |
|---|---|---|
| 1 | `verticals/` directory + manifest pattern | Unlocks per-tenant feature flags |
| 2 | Component macros (`table`, `modal`, `filter_bar`) | Cuts template size in half |
| 3 | Replace `filter_a…filter_h` with `extra` + index | Removes last migration-coupled pattern |
| 4 | Tenant config UI | Self-service onboarding |
| 5 | RBAC | Required before any external users |
| 6 | Audit log | Required for B2B trust |
| 7 | Billing model | Required before charging money |
| 8 | File attachments + CSV import/export | High customer demand |
| 9 | Public API + API keys | Ecosystem / integrations |
