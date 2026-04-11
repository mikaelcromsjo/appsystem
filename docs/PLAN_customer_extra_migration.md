# Plan: Move Customer & Product Specialized Fields to extra JSON

## Context

Customer model has 10 columns and Product model has 8 columns that are tenant-specific and hardcoded. Moving them to `extra` JSON enables truly dynamic per-tenant filters — tenants can define N filters via admin → data, and both customers and products use those same IDs as keys in their `extra` dicts.

**Customer fields to remove:**
- `code_name`, `controlled` (Booleans)
- `filter_a`–`filter_h` (8 Booleans) — customer's interest in filter categories

**Product fields to remove:**
- `type_a`–`type_h` (8 Booleans) — which filter categories this product belongs to

Both models already have `extra = MutableDict.as_mutable(JSON)`. Filter *definitions* (labels) are per-tenant via `TenantConfig` → `CmsConfig.filters`, editable in admin → data.

**No Alembic migration.** Drop all DB files and let `create_all()` at startup rebuild from the updated model.

**CMS filter ID alignment:** Update `cms-config-default.json` IDs from semantic names (`"parties"`) to `filter_a`–`filter_g`. These IDs become the shared keys in both `customer.extra` and `product.extra`, and the Alpine `productFilters` store. Adding a new filter in admin → data automatically works on both sides with no code changes.

---

## Files to Change

| File | Change |
|------|--------|
| `backend/data/cms-config-default.json` | Update filter IDs to `filter_a`–`filter_g` |
| `backend/models/product.py` | Remove `type_a`–`type_h` + update ProductUpdate schema |
| `backend/models/customer.py` | Remove 10 columns + update CustomerUpdate schema |
| `backend/routers/products.py` | Pass `filters_json`, `filters_map` from CmsConfig |
| `backend/templates/products/edit.html` | Loop over `filters_json`; use `extra.*` field names |
| `backend/templates/products/info.html` | Read types from `product.extra` |
| `backend/templates/calls/products_list.html` | Dynamic Alpine visibility from `product.extra` |
| `backend/templates/calls/product_info.html` | Read types from `product.extra` |
| `backend/functions/customers.py` | Extract and apply `extra.*` filter keys |
| `backend/templates/customers/edit.html` | Loop over `cms.filters`; use `extra.*` field names |
| `backend/templates/customers/filter.html` | Loop over `c_filters`; use `extra.*` field names |
| `backend/templates/calls/customer_calls.html` | Init Alpine store from `customer.extra` |
| `backend/core/static/js/base.js` | Init `productFilters` as empty `{}` |
| `backend/routers/admin.py` | CSV import: write filters to `extra` dict |

---

## Stage 0 — Product model + product templates (verify product side works)

**Goal:** Product uses `product.extra` for filter type flags instead of `type_a`–`type_h` columns. Product edit form and product info display driven by CMS filter list.

### 0a. `backend/models/product.py` — Product class
Remove columns: `type_a`, `type_b`, `type_c`, `type_d`, `type_e`, `type_f`, `type_g`, `type_h`

### 0b. `backend/models/product.py` — ProductUpdate schema
Remove same fields from `ProductUpdate`.

### 0c. `backend/templates/products/edit.html` (lines ~80–114)
Replace hardcoded type_a–type_g checkboxes with a dynamic loop over CMS filters.
The product edit route must pass `filters_json` (from `cms.filters`) to the template context.

```html
{% for item in filters_json %}
<label>
  <input type="hidden" name="extra.{{ item.id }}" value="false">
  <input type="checkbox" name="extra.{{ item.id }}" value="true"
    {% if product.extra and product.extra.get(item.id) %}checked{% endif %}/>
  {{ item.name | t }}
</label><br/>
{% endfor %}
```

### 0d. `backend/templates/products/info.html` (lines ~26–35)
Replace hardcoded `product.type_a` checks with a loop over CMS filters:
```html
{% set types = [] %}
{% for f in filters_map %}
  {% if product.extra and product.extra.get(f) %}
    {% set _ = types.append(filters_map[f]) %}
  {% endif %}
{% endfor %}
{{ types | join(', ') if types else 'None' }}
```

### 0e. `backend/templates/calls/products_list.html` (lines 37–44)
Replace hardcoded Alpine visibility expression with a Jinja-rendered dynamic OR chain.
The route must pass `cms_filters` list to this template's context.

```html
x-show="(
  {{ 'true' if product.extra_visilble_all else 'false' }} ||
  {% for f in cms_filters %}
    (Alpine.store('productFilters')['{{ f.id }}'] && {{ 'true' if product.extra and product.extra.get(f.id) else 'false' }})
    {% if not loop.last %} || {% endif %}
  {% endfor %}
) && ('{{ product.name.lower() }}'.includes(search.toLowerCase()))"
```

### 0f. `backend/templates/calls/product_info.html` (lines ~31–39)
Replace hardcoded `product.type_a` checks with loop over `filters_map` (same pattern as 0d).

### 0g. `backend/routers/products.py`
Add `cms: CmsConfig = Depends(get_cms_config)` to the product edit/info routes and pass `"filters_json": cms.filters` and `"filters_map": cms.filters_map` to template context.

**Test:** Drop DB → restart → create a product, tick some filter checkboxes → verify `product.extra = {"filter_a": true, ...}` in DB. Confirm product info shows correct filter labels.

---

## Stage 1 — Model + CMS config (verify DB recreates cleanly)

**Goal:** New DB has no filter columns on customers table.

### 1a. `backend/data/cms-config-default.json`
Update filter IDs:
```json
"filters": [
  {"id": "filter_a", "name": "Fester"},
  {"id": "filter_b", "name": "AW"},
  {"id": "filter_c", "name": "Föreläsningar"},
  {"id": "filter_d", "name": "Aktivism"},
  {"id": "filter_e", "name": "Konferenser"},
  {"id": "filter_f", "name": "Prenumeration"},
  {"id": "filter_g", "name": "Medlemskap"}
]
```

### 1b. `backend/models/customer.py` — Customer class
Remove these columns:
- `code_name`, `controlled`
- `filter_a`, `filter_b`, `filter_c`, `filter_d`, `filter_e`, `filter_f`, `filter_g`, `filter_h`

### 1c. `backend/models/customer.py` — CustomerUpdate schema
Remove same fields from `CustomerUpdate`.

**Test:** Drop DB files → restart app → verify customers table schema has no filter columns.

---

## Stage 2 — Customer edit form (verify save/load of filters via extra)

**Goal:** Customer edit form sends `extra.filter_a` etc., upsert route already handles `extra.*` → `data_dict["extra"]`.

### 2a. `backend/templates/customers/edit.html`

**code_name** (line ~47–48, change field name):
```html
<input type="hidden" name="extra.code_name" value="false">
<input type="checkbox" name="extra.code_name" value="true"
  {% if customer.extra and customer.extra.get('code_name') %}checked{% endif %} class="mr-2"/>
```

**controlled** (line ~155–156):
```html
<input type="hidden" name="extra.controlled" value="false">
<input type="checkbox" name="extra.controlled" value="true"
  {% if customer.extra and customer.extra.get('controlled') %}checked{% endif %} class="mr-2"/>
```

**filters loop** (lines ~164–177, change names and value access):
```html
{% for item in filters_json %}
<div class="mb-2">
  <label class="inline-flex items-center">
    <input type="hidden" name="extra.{{ item.id }}" value="false">
    <input type="checkbox" name="extra.{{ item.id }}" value="true"
      {% if customer.extra and customer.extra.get(item.id) %}checked{% endif %}
      class="mr-2"/>
    {{ item.name }}
  </label>
</div>
{% endfor %}
```

(`filters_json` is already passed from `customer_detail` route as `cms.filters`.)

**Test:** Create/edit customer, tick some filters → check `customer.extra` in DB contains the right keys/values. Reload edit form → checkboxes restore correctly.

---

## Stage 3 — Customer list filter (verify customer filtering by extra fields)

**Goal:** Customer list filter form sends `extra.filter_a`, `extra.controlled` etc. as session keys, and `get_user_customers()` applies Python-side filtering.

### 3a. `backend/templates/customers/filter.html`

Replace the hardcoded boolean preferences loop (lines ~208–227).

Remove the existing `code_name` select block (currently lines ~54–62), merge into the unified loop below:

```html
<!-- code_name -->
<div>
  <label class="block font-semibold">{{ "Code Name" | t }}</label>
  <select name="extra.code_name" class="border p-1 mt-1">
    <option value="">{{ "Any" | t }}</option>
    <option value="true" {% if filter_dict.get('extra.code_name') == 'true' %}selected{% endif %}>{{ "True" | t }}</option>
    <option value="false" {% if filter_dict.get('extra.code_name') == 'false' %}selected{% endif %}>{{ "False" | t }}</option>
  </select>
</div>

<!-- controlled + dynamic filters from CmsConfig -->
{% for field, label in [('controlled', 'Controlled')] + [(f.id, f.name) for f in c_filters] %}
<div>
  <label class="block font-semibold">{{ label }}</label>
  <select name="extra.{{ field }}" class="border p-1 mt-1">
    <option value="">{{ "Any" | t }}</option>
    <option value="true" {% if filter_dict.get('extra.' + field) == 'true' %}selected{% endif %}>{{ "True" | t }}</option>
    <option value="false" {% if filter_dict.get('extra.' + field) == 'false' %}selected{% endif %}>{{ "False" | t }}</option>
  </select>
</div>
{% endfor %}
```

### 3b. `backend/functions/customers.py` — `get_user_customers()`

After existing SQL + exact-match filtering, add Python-side `extra.*` boolean filtering:

```python
# Extra boolean filters (e.g. extra.filter_a = "true")
extra_bool = {
    k[6:]: v
    for k, v in filter_dict.items()
    if k.startswith("extra.") and v in ("true", "false")
}
if extra_bool:
    rows = [
        r for r in rows
        if all(
            bool((r.extra or {}).get(key)) == (v == "true")
            for key, v in extra_bool.items()
        )
    ]
```

**Test:** Filter customer list by filter_a=true → only customers with `extra["filter_a"] == True` returned.

---

## Stage 4 — Calls dashboard product visibility (verify Alpine filter store)

**Goal:** When a customer loads in calls dashboard, Alpine `productFilters` store is populated from `customer.extra`.

### 4a. `backend/templates/calls/customer_calls.html`

Replace lines 6–12 (hardcoded `customer.filter_a` access):
```js
{% for f in cms_filters %}
Alpine.store("productFilters")["{{ f.id }}"] = {{ (customer.extra or {}).get(f.id, false) | tojson }};
{% endfor %}
```

The route that renders `customer_calls.html` must pass `cms_filters`. Find the endpoint in `backend/routers/calls.py` and add:
- `cms: CmsConfig = Depends(get_cms_config)` to the function signature
- `"cms_filters": cms.filters` to the template context

### 4b. `backend/core/static/js/base.js`

Change the `productFilters` store init from the hardcoded object to empty:
```js
Alpine.store('productFilters', {});
```

Keys are populated per-customer from the template in 4a.

### 4c. `backend/templates/calls/dashboard.html` (lines ~77–84)

The label lookup `filters_map['filter_a']` now works correctly because filter IDs are `filter_a`, `filter_b`, etc. (after Stage 1). No structural change needed.

**Test:** Load customer with `extra.filter_a = true, filter_b = false` in calls dashboard → only products with `type_a = true` shown. Load another customer with different flags → product list updates.

---

## Stage 5 — Admin CSV import (verify import still works)

**Goal:** CSV import writes filter values to `customer.extra` instead of direct columns.

### 5a. `backend/routers/admin.py` (around line 278)

Replace direct column assignments with extra dict update:
```python
extra = {}
for col in ["filter_a", "filter_b", "filter_c", "filter_d", "filter_e", "filter_f", "filter_g", "filter_h"]:
    val = _parse_bool(row.get(col))
    if val is not None:
        extra[col] = val
if row.get("code_name") is not None:
    extra["code_name"] = _parse_bool(row.get("code_name"))
if row.get("controlled") is not None:
    extra["controlled"] = _parse_bool(row.get("controlled"))
customer.extra = extra
```

**Test:** Import a CSV with filter_a/filter_b columns → verify `customer.extra` populated correctly.
