# UI Patterns — Admin Verticals

Covers the `admin` and `global_admin` verticals. These use a sub-page navigation pattern (dashboard → detail pages) rather than a persistent tab layout.

---

## Page Structure

Admin content loads into `#admin_content` (or `#global_admin_content`). There is no persistent sidebar — navigation is done by replacing the content div entirely via HTMX.

```
Dashboard → Users / Scripts / Import / Data
```

---

## Dashboard (Sub-page Navigation)

The dashboard renders a row of navigation buttons. Each loads a sub-page into the content div.

```html
<h1 class="text-xl font-bold mb-4">Admin</h1>

<div class="flex gap-2">
  <button hx-get="{{ url_for('admin_users') }}" hx-target="#admin_content"
    class="px-3 py-1 border rounded bg-gray-100 hover:bg-gray-200">
    {{ "Users" | t }}
  </button>
  <button hx-get="{{ url_for('admin_script') }}" hx-target="#admin_content"
    class="px-3 py-1 border rounded bg-gray-100 hover:bg-gray-200">
    Script
  </button>
  …
</div>
```

These buttons are visually identical to toolbar buttons in user verticals: `px-3 py-1 border rounded bg-gray-100 hover:bg-gray-200`.

---

## Back Button

Every sub-page starts with a header bar containing a back button and a page title. The back button navigates to the dashboard.

```html
<div class="flex items-center gap-3 mb-4">
  <button
    hx-get="{{ url_for('admin_dashboard') }}"
    hx-target="#admin_content"
    class="px-3 py-1 border rounded bg-gray-100 hover:bg-gray-200 text-sm">
    ← {{ "Back" | t }}
  </button>
  <h2 class="text-lg font-bold">{{ "Page Title" | t }}</h2>

  <!-- Optional: action button on the far right -->
  <button @click="showCreate = !showCreate"
    class="px-3 py-1 border rounded bg-gray-100 hover:bg-gray-200 text-sm ml-auto">
    + {{ "New Item" | t }}
  </button>
</div>
```

- Back button: same button style, with `← ` prefix and `text-sm`.
- Title: `text-lg font-bold`, sits inline with the back button.
- Page-level action (e.g. "+ New User"): `ml-auto` to push to far right.

---

## Create Form (Collapsible)

New-record forms live above the table and are toggled with Alpine `showCreate`.

```html
<div x-data="{ showCreate: false }">

  <!-- header with back button and toggle button (see above) -->

  <div x-show="showCreate" x-transition class="mb-4 p-4 border rounded bg-gray-50">
    <form
      hx-post="{{ url_for('create_endpoint') }}"
      hx-target="#admin_content"
      hx-swap="innerHTML"
      class="flex gap-3 items-end flex-wrap">
      <div>
        <label class="block text-xs font-medium mb-1">{{ "Field" | t }}</label>
        <input type="text" name="field" required
          class="border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
      </div>
      <button type="submit"
        class="px-4 py-1.5 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm">
        {{ "Create" | t }}
      </button>
    </form>
  </div>

  <!-- table -->
</div>
```

- Wrapper: `p-4 border rounded bg-gray-50`.
- Form layout: `flex gap-3 items-end flex-wrap`.
- Labels: `text-xs font-medium mb-1`.
- Inputs: `border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400`.
- Submit: `px-4 py-1.5 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm`.

---

## Table

Same outer wrapper as user verticals:

```html
<div class="full-table">
  <table class="table-fixed w-full border overflow-x-auto">
    <thead>
      <tr>
        <th class="w-[5%] px-2 py-1 border">ID</th>
        <th class="w-[30%] px-2 py-1 border">{{ "Email" | t }}</th>
        …
        <th class="w-[10%] px-2 py-1 border text-center">{{ "Actions" | t }}</th>
      </tr>
    </thead>
    <tbody>
      {% for item in items %}
      <tr
        :class="{
          'bg-blue-50': selectedRow === {{ loop.index }},
          'hover:bg-gray-50': selectedRow !== {{ loop.index }}
        }"
        @click="selectedRow = {{ loop.index }}; $store.modal_admin.open = true"
        hx-get="{{ url_for('admin_item_detail', item_id=item.id) }}?list=short"
        hx-target="#modal-container-admin"
        hx-trigger="click"
        class="cursor-pointer align-top">

        <td class="px-2 py-2 border text-sm">…</td>
        …

        <!-- Command cell -->
        <td class="px-2 py-2 border text-center" @click.stop>
          <button
            hx-get="{{ url_for('admin_item_detail', item_id=item.id) }}"
            hx-target="#modal-container-admin"
            hx-swap="innerHTML"
            @click="$store.modal_admin.open = true"
            class="text-gray-500 hover:text-blue-600 text-base"
            title="{{ 'Edit' | t }}">✎</button>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
```

**Differences from user verticals:**
- Cell padding is `px-2 py-2` (taller rows) vs `px-2 py-1`.
- Selected row: `bg-blue-50` (lighter than user vertical's `bg-blue-100`).
- The command cell uses a bare **✎ icon** with no border/box — `text-gray-500 hover:text-blue-600 text-base`. No `border rounded` on the button.
- No search bar (admin tables tend to be short).

---

## Modals (Admin)

Admin verticals use the same `vertical_modal` component with `$store.modal_admin`. The pattern is identical to user verticals:

- Row click → `?list=short` → `item_info.html` (view-only, `submit = ''`)
- ✎ in command cell → no param → `item_edit.html` (editable, `submit = 'Save'`)

```html
<!-- item_info.html -->
<div x-init="$store.modal_admin.title = '{{ item.name }}'"></div>
<div x-init="$store.modal_admin.submit = ''"></div>
<div class="space-y-2 text-sm">
  <div><strong>{{ "Field" | t }}:</strong> {{ item.field }}</div>
  …
</div>

<!-- item_edit.html -->
<div x-init="$store.modal_admin.title = '{{ "Edit" | t }}: {{ item.name }}'"></div>
<div x-init="$store.modal_admin.submit = '{{ "Save" | t }}'"></div>
<form hx-post="…" hx-swap="none"
  x-init="
    $el.addEventListener('htmx:afterRequest', (event) => {
      if (event.detail.xhr.status === 200) {
        $store.modal_admin.open = false;
        htmx.ajax('GET', '{{ url_for('admin_items') }}', {target:'#admin_content', swap:'innerHTML'});
      }
    })
  ">
  …
</form>
```

After save, admin edit forms reload the full page into `#admin_content` (not just the tbody), since there is no separate rows endpoint.

---

## Inline Cell Edits

Admin tables use always-visible inline forms — no Alpine toggle state, no show/hide.

### Checkbox (auto-submit on change)

```html
<td class="px-2 py-2 border text-center" @click.stop>
  <form hx-post="…" hx-target="#admin_content" hx-swap="innerHTML">
    <input type="hidden" name="field" value="">
    <input type="checkbox" name="field" value="on"
      {% if item.field %}checked{% endif %}
      class="w-4 h-4"
      @change="$el.closest('form').requestSubmit()">
  </form>
</td>
```

No button. Change fires immediately.

### Single-value with pill + assign

Used for fields that hold one related record (e.g. Team).

```html
<td class="px-2 py-2 border text-sm" @click.stop>
  <!-- Current value as removable pill -->
  {% if item.related %}
  <div class="flex flex-wrap gap-1 mb-1">
    <form hx-post="{{ url_for('update_related', item_id=item.id) }}"
      hx-target="#admin_content" hx-swap="innerHTML" class="inline">
      <input type="hidden" name="related_id" value="">
      <button type="submit"
        class="px-2 py-0.5 bg-blue-100 border border-blue-300 rounded text-xs hover:bg-red-100 hover:border-red-300"
        title="{{ 'Click to remove' | t }}">
        {{ item.related.name }} ✕
      </button>
    </form>
  </div>
  {% endif %}
  <!-- Assign form -->
  <form hx-post="{{ url_for('update_related', item_id=item.id) }}"
    hx-target="#admin_content" hx-swap="innerHTML"
    class="flex gap-1">
    <select name="related_id" class="border rounded px-1 py-0.5 text-xs">
      <option value="">— {{ "None" | t }} —</option>
      {% for opt in options %}
      {% if item.related_id != opt.id %}
      <option value="{{ opt.id }}">{{ opt.name }}</option>
      {% endif %}
      {% endfor %}
    </select>
    <button type="submit"
      class="px-2 py-0.5 border rounded bg-gray-100 hover:bg-gray-200 text-xs">
      {{ "Set" | t }}
    </button>
  </form>
</td>
```

Only unassigned options appear in the select (current is excluded).

### Multi-value with pills + add

Used for fields that hold multiple related values (e.g. Roles, Tenants).

```html
<td class="px-2 py-2 border" @click.stop>
  <!-- Removable pills -->
  <div class="flex flex-wrap gap-1 mb-1">
    {% for val in item.values %}
    <form hx-post="{{ url_for('remove_val', item_id=item.id) }}"
      hx-target="#admin_content" hx-swap="innerHTML" class="inline">
      <input type="hidden" name="val_id" value="{{ val.id }}">
      <button type="submit"
        class="px-2 py-0.5 bg-blue-100 border border-blue-300 rounded text-xs hover:bg-red-100 hover:border-red-300"
        title="{{ 'Click to remove' | t }}">
        {{ val.name }} ✕
      </button>
    </form>
    {% endfor %}
  </div>
  <!-- Add form (only shown when unassigned options exist) -->
  {% if available %}
  <form hx-post="{{ url_for('add_val', item_id=item.id) }}"
    hx-target="#admin_content" hx-swap="innerHTML"
    class="flex gap-1">
    <select name="val_id" class="border rounded px-1 py-0.5 text-xs">
      {% for opt in available %}
      <option value="{{ opt.id }}">{{ opt.name }}</option>
      {% endfor %}
    </select>
    <button type="submit"
      class="px-2 py-0.5 border rounded bg-gray-100 hover:bg-gray-200 text-xs">
      {{ "Add" | t }}
    </button>
  </form>
  {% endif %}
</td>
```

---

## Feedback Messages

Success and error messages render above the table, disappearing on next load (they're part of the full-page swap).

```html
{% if error %}
<div class="mb-3 px-3 py-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
  {{ error }}
</div>
{% endif %}

{% if saved %}
<div class="mb-3 px-3 py-2 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
  {{ "Saved." | t }}
</div>
{% endif %}
```

Admin pages return the full page HTML on every mutation (no partial swap), so feedback is passed as template context.
