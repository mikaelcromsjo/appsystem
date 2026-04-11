# Modularity Refactor — Implementation Plan

Branch: `feature/modularity`

## Goal

Move toward self-contained vertical packages:

```
backend/verticals/<slug>/
  __init__.py        # manifest (already exists)
  router.py          # move from routers/<slug>.py
  templates/         # move from templates/<slug>/
```

Per-vertical **non-blocking modals**: switching tabs does not close the modal
of the previous vertical (e.g. a customer detail can remain open while
the user works in the calls tab).

---

## Design: Per-vertical non-blocking modals

### Why the current single modal breaks this

The global `$store.modal` controls one shared `<div>` in `base.html`.
When the user clicks a nav button the *vertical tab* switches — the modal
content div is shared, so the old content disappears and the store state is
mixed between verticals.

### Solution

Give every vertical its **own modal container** at the `<body>` level
(i.e. **not** inside the `x-show` content div). Each modal:

- Has a unique DOM id: `modal-container-customers`, `modal-container-calls`, …
- Has a unique Alpine store: `$store.modal_customers`, `$store.modal_calls`, …
- Is always in its own tab.

Switching the active tab hides the *content panel* and the modal

```
body
  ├─ header (nav tabs)
  ├─ main
  │    ├─ #customer_content  (x-show="active==='customers'")
  │    ├─ #calls_content     (x-show="active==='calls'")
  │    └─ …
  ├─ #modal-customers        ← fixed, always in DOM  ← NEW
  ├─ #modal-calls            ← fixed, always in DOM  ← NEW
  └─ …
```

Templates within a vertical reference their own store/id:

```html
<!-- customers/list.html -->
hx-target="#modal-container-customers"
@click="$store.modal_customers.open = true"
```

A Jinja2 variable `modal_store` and `modal_target` is passed per vertical
so templates stay DRY:

```python
# routers/customers.py
MODAL = {"store": "modal_customers", "target": "#modal-container-customers"}
# pass MODAL into every render() call
```

```html
<!-- customers/edit.html — works regardless of which vertical calls it -->
hx-target="{{ modal.target }}"
@click="{{ modal.store }}.open = true"
```

---

## Steps (each independently testable)

---

### Step 0 — Create branch

```
git checkout -b feature/modularity
```

Nothing changes yet; verify app still starts.

---

### Step 1 — Per-vertical modal containers in `base.html`

**What changes:** `base.html` — add one modal `<div>` per vertical **below** `</main>`, above the existing global modal.

Template loop:

```html
{% for v in nav_verticals %}
<div id="modal-{{ v.slug }}"
     x-data
     x-show="$store['modal_{{ v.slug }}'].open"
     x-transition.opacity
     @keydown.escape.window="$store['modal_{{ v.slug }}'].open = false"
     class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
     style="display:none">
  <div class="bg-white rounded-xl shadow-lg w-full max-w-7xl mx-4 flex flex-col"
       style="max-height:90vh;overflow:hidden">
    <!-- header -->
    <div class="flex justify-between items-center p-4 border-b flex-shrink-0">
      <h5 class="text-lg font-semibold"
          x-text="$store['modal_{{ v.slug }}'].title"></h5>
      <button type="button"
              class="text-gray-500 hover:text-gray-700 p-1 rounded"
              @click="$store['modal_{{ v.slug }}'].open = false">✕</button>
    </div>
    <!-- body -->
    <div id="modal-container-{{ v.slug }}"
         class="p-4 overflow-y-auto flex-grow"
         style="min-height:0"
         x-effect="if ($store['modal_{{ v.slug }}'].open) $nextTick(() => { $el.scrollTop = 0; })">
    </div>
    <!-- footer -->
    <div class="p-4 border-t flex-shrink-0 flex justify-end gap-2">
      <button type="button"
              class="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
              @click="$store['modal_{{ v.slug }}'].open = false">
        {{ "Close" | t }}
      </button>
      <template x-if="$store['modal_{{ v.slug }}'].submit">
        <button type="button"
                class="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-500"
                @click="document.querySelector('#modal-container-{{ v.slug }} form').requestSubmit()">
          <span x-text="$store['modal_{{ v.slug }}'].submit"></span>
        </button>
      </template>
    </div>
  </div>
</div>
<!-- clear title/submit when closed -->
<div x-data
     x-effect="if (!$store['modal_{{ v.slug }}'].open) {
       $store['modal_{{ v.slug }}'].title = '';
       $store['modal_{{ v.slug }}'].submit = '';
     }"></div>
{% endfor %}
```

Keep the old global modal in place until Step 3 (backward compat).

**Test:** App starts, no JS errors. Old modal still works. No visual change yet.

---

### Step 2 — Per-vertical Alpine stores in `base.js`

**What changes:** `core/static/js/base.js` — register one store per vertical.

Because `base.js` is static, the store names must be hardcoded or generated
server-side. Simplest: generate the store init block from the Jinja2 template
as an inline `<script>` in `base.html`:

```html
<!-- base.html, after Alpine.js script tag -->
<script>
  document.addEventListener('alpine:init', () => {
    {% for v in nav_verticals %}
    Alpine.store('modal_{{ v.slug }}', { title: '', submit: '', open: false });
    {% endfor %}
  });
</script>
```

This replaces the need to add stores in `base.js`.

**Test:** Open DevTools → Alpine → Stores; confirm `modal_customers`, `modal_calls`, etc. are visible. Old `modal` store still present.

---

### Step 3 — Migrate `customers` vertical to its own modal

**What changes:** `routers/customers.py`, `templates/customers/*.html`

1. Add `MODAL_STORE = "modal_customers"` and
   `MODAL_TARGET = "#modal-container-customers"` constants to `routers/customers.py`.
2. Pass `modal={"store": MODAL_STORE, "target": MODAL_TARGET}` in every
   `render()` call in `customers.py`.
3. In all `templates/customers/` templates, replace:
   - `hx-target="#modal-container"` → `hx-target="{{ modal.target }}"`
   - `$store.modal.open = true` → `$store.{{ modal.store }}.open = true`
   - `$store.modal.title` → `$store.{{ modal.store }}.title`
   - `$store.modal.submit` → `$store.{{ modal.store }}.submit`
   - `$store.modal.open = false` → `$store.{{ modal.store }}.open = false`


---

### Step 4 — Migrate remaining verticals

Repeat Step 3 for each vertical in this order (least risky first):

1. `companies`
2. `invoices`
3. `accounts`
4. `products`
5. `calls`
6. `alarms`
7. `admin`

**Test after each:** Vertical's own edit modal opens; 

---

### Step 5 — Remove old global modal

**What changes:** `base.html`

Remove the old `<!-- Global Modal Container -->` block and the
`x-effect` that clears `$store.modal.*`.

Remove `Alpine.store('modal', …)` from `base.js`.

**Test:** No references to `#modal-container` (without slug suffix) remain.
Run a full smoke test across all verticals.

---

### Step 6 — Shared component macro `templates/components/modal.html`

Extract the per-vertical modal HTML from Step 1 into a Jinja2 macro:

```html
{# templates/components/modal.html #}
{% macro vertical_modal(v) %}
<div id="modal-{{ v.slug }}" …>…</div>
{% endmacro %}
```

In `base.html`:

```html
{% from "components/modal.html" import vertical_modal %}
{% for v in nav_verticals %}
  {{ vertical_modal(v) }}
{% endfor %}
```

**Test:** No visual change; identical DOM.

---

### Step 7 — Move templates into vertical directories

**What changes:** Jinja2 loader, template files.

1. Update `backend/templates.py` (Jinja2 loader setup) to add a secondary
   loader that checks `verticals/<slug>/templates/` before falling back to
   `templates/`:

   ```python
   from jinja2 import ChoiceLoader, FileSystemLoader
   # Add vertical template dirs
   vertical_dirs = [p / "templates" for p in verticals_path.iterdir()
                    if (p / "templates").is_dir()]
   loader = ChoiceLoader([FileSystemLoader(vertical_dirs + [templates_dir])])
   ```

2. Migrate one vertical at a time — start with `companies` (smallest):
   - Create `verticals/companies/templates/companies/`
   - Move `templates/companies/*.html` there.
   - Delete the old directory.

**Test after each migration:** Vertical renders correctly.

---

### Step 8 — Move routers into vertical directories

**What changes:** One vertical at a time. Start with `companies`.

1. Copy `routers/companies.py` → `verticals/companies/router.py`
   (no content changes yet).
2. Update `verticals/companies/__init__.py`:
   ```python
   def get_routers():
       from verticals.companies import router
       return [router.router]
   ```
3. Delete `routers/companies.py`.

**Test:** Companies CRUD works. `url_for()` still resolves.

Repeat for all verticals. `routers/auth.py`, `routers/user.py`, `routers/admin.py`
stay in `routers/` (they are shared infrastructure, not vertical-specific).

---

### Step 9 — Schema-driven list pages (optional, later phase)

Add `COLUMNS` to each vertical `__init__.py`:

```python
COLUMNS = [
    {"key": "name",   "label": "Name",    "sortable": True},
    {"key": "status", "label": "Status",  "sortable": True},
]
```

Pass via context:

```python
from verticals import companies as v_companies
render("companies/list.html", {"columns": v_companies.COLUMNS, …})
```

Create `templates/components/table.html` generic table macro.

---

## Milestone summary

| Step | Testable outcome |
|------|-----------------|
| 0 | Branch created, app starts |
| 1 | Per-vertical modal DOM present, no behaviour change |
| 2 | Per-vertical Alpine stores registered |
| 3 | Customers modal non-blocking (stays open on tab switch) |
| 4 | All verticals non-blocking |
| 5 | Old global modal removed |
| 6 | Modal extracted to reusable macro |
| 7 | Templates co-located with verticals |
| 8 | Routers co-located with verticals |
| 9 | Schema-driven list columns |
