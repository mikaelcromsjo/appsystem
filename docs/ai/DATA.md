# Data conventions

Columns and relations: read `backend/models/`. This file lists value shapes the
templates and filters silently depend on.

## Value shapes

| Field | Shape |
|---|---|
| `Call.status` | plain integer in a JSON column: `1` answer, `2` no answer, `3` outside call. A list breaks the row colouring. |
| `ProductCustomer.status` | `1` interested, `2` not interested, `3` coming |
| `ProductCustomer.type_status` | integer; holds a CMS product-type item id, so those ids must be numeric strings (`"4"`…`"7"`; totals exist for `s1`–`s7`) |
| `Invoice.extra.status` | **string** `"1"` processing, `"2"` OK, `"3"` cancelled. Must be set — the row template emits broken JS without it. |
| `Invoice.date` | required |
| `Invoice.number` | assigned from the `InvoiceNumber` autoincrement when status becomes `"2"` |
| `Invoice.extra.row` | `{"1": {"description", "price", "qty"}, …}` with string values |
| Bool extras | the string `"true"`; the JSON filter matches that, not JSON `true` |
| Datetimes | naive UTC; convert with `local_to_utc` / `utc_to_local` |

- Invoice sender = the invoice's team: `team.name` plus address/VAT/bank fields in
  `team.extra`. `Company.extra.company_name` is what lists and PDFs show.
- Invoice PDFs are written to `backend/pdfs/invoice_<id>.pdf` — tracked in git, not
  tenant-scoped (two tenants with the same invoice id share a file), regenerated on
  every PDF request.

## CMS config

Per-tenant JSON: table `config`, key `cms` (categories, product types,
organisations, filters, personalities, extra-field definitions). Inject with
`cms: CmsConfig = Depends(get_cms_config)` (`data/constants.py`).

- The global default lives in master `global_config`; new tenants copy it.
  `data/cms-config-default.json` only seeds that default.
- Organisation and personality ids must be **integers** (templates look them up as
  ints). `cms-config-default.json` uses string ids, so with it those fields do not
  render; the demo tenants use `DEMO_CMS` from `scripts/demo_data.py` instead.
- The module-level maps in `data/constants.py` (`categories_map`, …) come from the
  default file, not from the tenant. Use the injected `CmsConfig`.

## Upsert conventions

- The request body is JSON validated by the permissive `Update` model
  (`extra = "allow"`), so unknown keys pass through; typing happens in
  `populate(data, record, <Entity>Update)` — see `core/functions/populate.py.md`.
- Extra fields arrive as flat keys `"extra.<key>"` and must be folded into
  `data["extra"]` before `populate()`.
- Pop foreign-key / relationship fields before `populate()` and set them afterwards.
- `Model.empty()` builds an unsaved instance with type-based blanks for "new" forms.

## List filters

Filters are stored per vertical in the session (e.g. `customer_filters`) and turned
into SQL by `build_filters()` — see `core/functions/filters.py.md`. It returns SQL
expressions mixed with `{"exact_vals", "column"}` dicts that must be applied in
Python after the query. Extra fields are filterable only when their definitions are
passed as `json_fields`.

## Tags

Polymorphic: `TagLink(tag_id, object_id, object_type)` with `object_type` a plain
string such as `"customer"`; no foreign key to the tagged row.
