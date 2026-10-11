# UI contracts (templates, HTMX, Alpine, CSS)

## Page shell

`/dashboard` renders `base.html` once: one nav button, one content `<div>` and one
modal per vertical. Tabs are shown and hidden client side (Alpine `active`, kept in
`localStorage.activeTab`); each tab's content is fetched by HTMX into its
`content_div_id`. There is no per-page URL — `hx-push-url` is off.

Consequences:

- A fragment must work when swapped into its content div; it never gets its own
  `<html>`. Global markup (dialogs, toasts) belongs in `base.html`.
- `base.js` is loaded once, at the end of `base.html`. Code that must run for
  swapped-in content goes in an `htmx:afterSwap` listener or an Alpine `x-init`.
- Mobile call mode (`/calls/number`) uses `base_mobile.html` and `mobile.js`
  instead; it does not load `base.js`. On a mobile user agent `base.js` asks
  "Open in call mode?" once per login (`localStorage.callModeAnswered`, cleared
  by `login.html`).

## Server → client signals

| Mechanism | Effect |
|---|---|
| Response header `HX-Trigger: <slug>RowsReload` | the list's `<tbody>` re-fetches its rows (`hx-trigger="<slug>RowsReload from:body"`) |
| `HX-Trigger: customersReload` / `productsReload` / `alarmsReload` / `calls…Reload` | whole-tab reloads wired by hand at the bottom of `base.js` — a new event name needs a listener there |
| Response header `HX-Popup-Message: <text>` | toast; red when status ≥ 400 |
| JSON body with `detail` | toast; a FastAPI validation list also marks the named fields (`showValidationErrors`) |
| Any other response ≥ 400 | toast "Unexpected server response" |

After a save, return an empty response with `HX-Trigger` rather than re-rendering
the list. Admin and global-admin sub-pages are the exception: every action returns
the whole sub-page and passes feedback (`error`, `saved`) as template context.

## Modal per vertical

`components/modal.html` renders `#modal-<slug>` with body `#modal-container-<slug>`,
driven by `Alpine.store('modal_<slug>')` = `{title, submit, open, ready}`.

- Open: `hx-get=… hx-target="#modal-container-<slug>"` plus
  `@click="$store.modal_<slug>.open = true"`. The modal becomes visible only when
  `ready` is set, which `base.js` does after the swap — no manual show needed.
- The loaded fragment sets `title` and `submit` in `x-init`. A non-empty `submit`
  shows the footer button, which calls `requestSubmit()` on the **first `<form>`**
  in the container; an info view sets `submit = ''`.
- The fragment closes the modal itself after a successful save (`open = false`)
  and triggers the rows reload.
- Row click → info view (`?list=short`); the last "command" cell uses `@click.stop`
  so its buttons do not also open the row.

Destructive buttons: `x-confirm="message"` with `hx-trigger="confirmed"`.

## Tables

- Lists sit in `<div class="full-table">` (styles in `base.html`): a 55vh scroll
  box. Cells cut long text with "…" and `base.js` adds the full text as a tooltip.
  The `<thead>` is sticky **without a z-index** on purpose, so menus and dialogs
  always paint above it; do not add one.
- Client-side search is `searchTable()` in `base.js`; it only hides rows already
  rendered.

## Tailwind

- `backend/core/static/css/tailwind.css` is a **committed, purged build**, not the
  CDN. A class that is not already used somewhere does nothing until you rebuild:
  `node node_modules/tailwindcss/lib/cli.js -i backend/core/static/css/input.css -o backend/core/static/css/tailwind.css --minify`
- `tailwind.config.js` replaces the default palette: only `gray`, `red`, `yellow`,
  `green`, `blue`, `indigo`, `purple`, `pink` (custom shades) plus black/white exist.
  `bg-orange-500`, `text-teal-600` etc. never render.
- Classes built in Python or JS strings are picked up only if the full class name
  appears literally in a file under `backend/`.

## Translations

`{{ "English text" | t }}` — the English string is the key; Swedish is the only
language (`backend/core/lang/lang_sv.json`).

- An unknown key is appended to `lang_sv.json` at render time with the English text
  as its value, and the file is rewritten from memory. **A manual edit made while
  the app is running can be overwritten** by the next unknown key.
- A literal `{{ "…" | t }}` is evaluated when the template is **compiled**, not per
  request. After changing a translation the old text stays until the template is
  recompiled.
- Reliable sequence for a new label: add the key and Swedish value to
  `lang_sv.json`, then restart the app (`docker restart appsystem`, or save any
  `.py` file) before the page is rendered. If it was already rendered, fix the
  value, restart, and check the file kept your value.

## Jinja limits

Jinja is not Python: no bitwise operators (use `| bitand(x)`), no comprehensions,
no f-strings, no walrus. Show datetimes with `| date` (UTC → Europe/Stockholm).
