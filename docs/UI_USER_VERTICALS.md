# UI Patterns — User Verticals

Covers verticals rendered inside the main content area (customers, products, alarms, etc.).

---

## Page Structure

A user vertical loads into its `content_div_id` (e.g. `#customers_content`) via HTMX on tab activation. The top level is a single `<div>` wrapping the list view and its toolbar.

```html
<div id="customer-container">
  <div id="customer-list" x-data="{ selectedRow: 0 }">
    <!-- search bar -->
    <!-- table -->
    <!-- toolbar (New, Filter, Clear Filter, …) -->
  </div>
</div>
```

---

## Table

```html
<div class="full-table">
  <table class="table-fixed w-full border overflow-x-auto">
    <thead>
      <tr>{{ table_head_row(columns) }}</tr>
    </thead>
    <tbody id="customers-tbody"
      hx-get="{{ url_for('customers_rows') }}"
      hx-trigger="customersRowsReload from:body"
      hx-swap="innerHTML">
      {% include "customers/rows.html" %}
    </tbody>
  </table>
</div>
```

- Wrapper: `full-table` (handles horizontal scroll).
- `table-fixed w-full border overflow-x-auto` on `<table>`.
- `<thead>` uses the `table_head_row(columns)` macro from `components/table.html`.
- `<tbody>` is a named HTMX reload target — reloads on a custom event (`customersRowsReload from:body`).

### Row (`rows.html`)

```html
{% for item in items %}
<tr
  hx-get="{{ url_for('item_detail', item_id=item.id) }}?list=short"
  hx-target="#modal-container-<slug>"
  hx-trigger="click"
  :class="{
    'bg-blue-100 font-bold text-blue-600': selectedRow === {{ loop.index }},
    'bg-white hover:bg-gray-100 text-gray-900': selectedRow != {{ loop.index }}
  }"
  class="cursor-pointer"
  @click="selectedRow = {{ loop.index }}; $store.modal_<slug>.open = true">

  <td class="px-2 py-1 border">…</td>
  …

  <!-- Command cell — always last, @click.stop -->
  <td class="px-2 py-1 border text-center" @click.stop>
    <button hx-get="{{ url_for('item_detail', item_id=item.id) }}"
      hx-target="#modal-container-<slug>" hx-swap="innerHTML"
      @click="$store.modal_<slug>.open = true">
      {{ "Edit" | t }}
    </button>
    <button hx-post="{{ url_for('delete_item', item_id=item.id) }}"
      hx-trigger="confirmed"
      x-confirm="{{ 'Are you sure?' | t }}">
      {{ "Delete" | t }}
    </button>
  </td>
</tr>
{% endfor %}
```

**Rules:**
- Clicking a row opens the **info modal** (`?list=short` → `info.html`).
- Clicking the command cell (last column) does NOT propagate to the row (`@click.stop`).
- The edit button in the command cell opens the **edit modal** (no `?list=short`).
- Selected row is highlighted `bg-blue-100 font-bold text-blue-600`.
- Cell padding: `px-2 py-1`.

### Cell widths

Defined with Tailwind `w-[N%]` on `<th>`. Total must equal 100%. Example:

```html
<th class="w-[5%] …">   <!-- index / ID -->
<th class="w-[30%] …">  <!-- primary field -->
<th class="w-[10%] …">  <!-- command cell -->
```

---

## Search Bar

Client-side row filtering via `searchTable()` Alpine component.

```html
<div x-data="searchTable()">
  <div class="relative my-2">🔎︎
    <input type="text"
      placeholder="{{ 'Search name, number or phone.' | t }}"
      class="w-[400px] border border-gray-300 rounded pl-4 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      x-model="query"
      @input.debounce.300ms="filterRows()">
  </div>
  <!-- table goes here -->
</div>
```

- Width: `w-[400px]` fixed.
- Debounce: `300ms`.
- Icon: plain `🔎︎` text before the input, no wrapper.

---

## Toolbar

Lives below the table. Buttons use the same base style throughout:

```
px-3 py-1 border rounded bg-gray-100 hover:bg-gray-200
```

```html
<div class="mt-2 flex gap-2">
  <button … class="px-3 py-1 border rounded bg-gray-100 hover:bg-gray-200">
    {{ "New Item" | t }}
  </button>

  <button hx-get="{{ url_for('item_filter') }}"
    hx-target="#modal-container-<slug>"
    @click="$store.modal_<slug>.open = true"
    class="px-3 py-1 border rounded bg-gray-100 hover:bg-gray-200">
    {{ "Filter" | t }}
  </button>

  <button hx-post="{{ url_for('set_filter') }}" hx-target="#<slug>-tbody" hx-swap="innerHTML"
    hx-ext="json-enc"
    class="px-3 py-1 border rounded bg-gray-100 hover:bg-gray-200">
    {{ "Clear Filter" | t }}
  </button>
</div>
```

- **New**: opens edit modal with `item_id=0`.
- **Filter**: opens filter form in modal.
- **Clear Filter**: POST to reset, reloads tbody directly.

---

## Modals

The vertical modal component (`components/modal.html`) renders once per vertical in `base.html`. It is controlled via the Alpine store `$store.modal_<slug>`.

### Opening a modal

```html
hx-get="<url>"
hx-target="#modal-container-<slug>"
hx-swap="innerHTML"
@click="$store.modal_<slug>.open = true"
```

The loaded fragment sets the modal title and submit button via `x-init`:

**info.html** (view only — no submit button):
```html
<div x-init="$store.modal_<slug>.title = '{{ item.name }}'"></div>
<div x-init="$store.modal_<slug>.submit = ''"></div>
```

**edit.html** (shows Save button):
```html
<div x-init="$store.modal_<slug>.title = '{{ item.name }}'"></div>
<div x-init="$store.modal_<slug>.submit = '{{ "Save" | t }}'"></div>
```

The modal's Save button calls `document.querySelector('#modal-container-<slug> form').requestSubmit()`.

### Closing after save

```html
<form
  hx-post="…"
  hx-swap="none"
  x-init="
    $el.addEventListener('htmx:afterRequest', (event) => {
      if (event.detail.xhr.status === 200) {
        $store.modal_<slug>.open = false;
        htmx.trigger(document.body, '<slug>RowsReload');
      }
    })
  ">
```

---

## Filter Form (`filter.html`)

Loaded into modal. Uses same `edit.html`-style `x-init` for title/submit, but POSTs to a filter endpoint and closes on success.

---

## Inline Cell Edits

Some cells support quick edits without opening a modal. Follow the global_admin `globalusers.html` pattern:

- **No toggle state** — forms/controls are always visible.
- **Checkbox fields** auto-submit on `@change`:

```html
<td @click.stop>
  <form hx-post="…" hx-target="#<slug>_content" hx-swap="innerHTML">
    <input type="hidden" name="field" value="">
    <input type="checkbox" name="field" value="on"
      {% if item.field %}checked{% endif %}
      class="w-4 h-4"
      @change="$el.closest('form').requestSubmit()">
  </form>
</td>
```

- **Multi-value pill fields** — each assigned value is a removable pill, with an add form below:

```html
<td @click.stop>
  <!-- Existing values as removable pills -->
  <div class="flex flex-wrap gap-1 mb-1">
    {% for val in item.values %}
    <form hx-post="{{ url_for('remove_val', item_id=item.id) }}" hx-target="…" class="inline">
      <input type="hidden" name="value_id" value="{{ val.id }}">
      <button type="submit"
        class="px-2 py-0.5 bg-blue-100 border border-blue-300 rounded text-xs hover:bg-red-100 hover:border-red-300"
        title="{{ 'Click to remove' | t }}">
        {{ val.name }} ✕
      </button>
    </form>
    {% endfor %}
  </div>
  <!-- Add form -->
  <form hx-post="{{ url_for('add_val', item_id=item.id) }}" hx-target="…" class="flex gap-1">
    <select name="value_id" class="border rounded px-1 py-0.5 text-xs">
      {% for opt in available_options %}
      <option value="{{ opt.id }}">{{ opt.name }}</option>
      {% endfor %}
    </select>
    <button type="submit" class="px-2 py-0.5 border rounded bg-gray-100 hover:bg-gray-200 text-xs">
      {{ "Add" | t }}
    </button>
  </form>
</td>
```

Pill hover turns red to signal destructive action. Inline edit cells always use `@click.stop`.
