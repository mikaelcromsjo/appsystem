# Demo Data

The demo data is what a visitor sees after logging in from the landing page, and
what developers test against. All people, companies, phone numbers and bank
details are fictional (emails use the reserved `.example` TLD, phone numbers the
ranges PTS reserves for fiction).

- Records: `backend/scripts/demo_data.py` (pure data, edit this to change the demo)
- Seeder: `backend/scripts/generate_test_data.py`

## Seeding

```bash
# inside the container, from backend/
docker exec -w /app/backend appsystem python scripts/generate_test_data.py           # seed if missing
docker exec -w /app/backend appsystem python scripts/generate_test_data.py --reset   # wipe and seed again
```

- On startup `seed_test_data()` seeds an empty database. It skips a tenant that is
  already seeded (config key `demo_seed`) and never touches a database that holds
  customers from elsewhere — that needs `--reset`.
- `--reset` deletes **all** business records, teams (except `Admin`), accounts and
  demo users in the two demo tenants, then seeds again. Other tenants and other
  logins are left alone.
- All dates are relative to the day of seeding: products and alarms are in the
  future, calls and invoices in the recent past. The products tab hides products
  five days after their end date and the alarms tab hides past alarms, so run
  `--reset` now and then to keep the demo fresh.

## Logins

Password for all demo users: `1234`. Login is by **email** (the login form
rejects anything that is not an email address). Both demo tenants have 2FA off.

| Email | Name | Team | Admin | Roles | Tenants |
|-------|------|------|-------|-------|---------|
| `sales@nordljus.example` | Sara Nyström | Kundtjänst | no | customers, products | Nordljus |
| `jonas.berg@nordljus.example` | Jonas Berg | Kundtjänst | no | customers, products | Nordljus |
| `anna.lindqvist@nordljus.example` | Anna Lindqvist | Kundtjänst | **yes** | customers, products | Nordljus + Fjällvind |
| `finance@nordljus.example` | Oskar Dahl | Ekonomi | no | customers, companies, invoices | Nordljus |
| `maria.sandberg@nordljus.example` | Maria Sandberg | Ekonomi | no | customers, companies, invoices | Nordljus |
| `karin.ekstrom@nordljus.example` | Karin Ekström | Ekonomi | **yes** | customers, companies, invoices | Nordljus + Fjällvind |
| `partner@nordljus.example` | Linnea Åkesson | Partnerförsäljning | no | customers, products, companies, invoices | Nordljus |

`sales@…`, `finance@…` and `partner@…` are the logins shown on the landing page. Anna and
Karin belong to both tenants, so they get the tenant picker after login.
`admin@localhost` (superadmin, from `ADMIN_EMAIL`) has access to both tenants.

What each kind of user sees:

- **Non-admin caller** (`sales`): Customers tab = customers assigned to them (6);
  Call Center = all customers of their team (8); Alarms = their team's alarms.
  Companies and Invoices are empty, since those belong to team Ekonomi.
- **Non-admin finance** (`finance`): Companies and Invoices of team Ekonomi.
  No customers or alarms.
- **Non-admin with both** (`partner`): team Partnerförsäljning owns its own customers
  (3, all assigned to her), alarms (2), companies (2) and invoices (3), so every tab
  has content without admin rights.
- **Admin** (`anna`, `karin`): everything in the tenant, plus the Admin tab.

## Tenant 1 — Nordljus Media AB (slug `default`)

A media house that sells events, a magazine subscription, memberships and a course,
with a call center team and a finance team.

| Table | Count | Notes |
|-------|-------|-------|
| Accounts | 4 | Nordljus Media AB, Event, Förlag, Stipendiestiftelse — address, VAT and bank details filled |
| Teams | 3 (+ `Admin`) | Kundtjänst, Ekonomi, Partnerförsäljning — `extra` holds the sender details printed on invoices |
| Users | 7 | see above; profile and bank details filled |
| Products | 6 | 3 events, 1 subscription, 1 membership, 1 course — all with type extras and filters |
| Customers | 13 | 8 in team Kundtjänst (6 assigned to `sales`, 2 to `jonas.berg`), 3 in Partnerförsäljning (`partner`), 2 unassigned (Sofia Bergqvist, Viktor Nordin) |
| Product selections | 24 | interested / not interested / coming, with type status and order date |
| Calls | 19 | answered, no answer and outside calls, with notes |
| Alarms | 8 | all upcoming, each tied to a customer and a product |
| Companies | 7 | Swedish and one Danish, with contact, address and org number |
| Invoices | 10 | 6 OK, 1 cancelled, 3 processing; SEK and EUR; 1–2 rows each |
| Tags | 12 | also in the tag tables, for autocomplete |

## Tenant 2 — Fjällvind Event AB (slug `fjallvind`)

A smaller outdoor-events company, there to show tenant isolation. Seeded only when
the default database is SQLite (the tenant gets its own file next to it).

4 accounts, 2 teams (Bokning, Ekonomi), 2 users (Anna, Karin), 4 products,
5 customers (1 unassigned), 8 selections, 5 calls, 4 alarms, 4 companies, 5 invoices.

## CMS config

Both demo tenants get their own CMS config (`DEMO_CMS` in `demo_data.py`) instead of
`data/cms-config-default.json`. The ids are chosen to match what the templates expect:

- **Product type item ids are numeric strings** (`"4"`–`"7"`). They are stored in the
  integer column `ProductCustomer.type_status`, after the fixed statuses 1–3.
- **Organisation and personality ids are integers** — the info views look them up as ints.
- Bool extras are stored as the string `"true"` (what the forms post and the filter matches).

## Field conventions used by the seeder

| Field | Values |
|-------|--------|
| `Call.status` | integer: `1` answer, `2` no answer, `3` outside call |
| `ProductCustomer.status` | `1` interested, `2` not interested, `3` coming |
| `ProductCustomer.type_status` | item id of the product's type, only when status is `3` |
| `Invoice.extra.status` | string: `"1"` processing, `"2"` OK (has a number), `"3"` cancelled |
| `Invoice.extra.row` | `{"1": {"description", "price", "qty"}, …}` with string values |
| `Customer.organisations` | list of organisation ids as strings |
| `Customer.last_call_date` | date of the latest answered or outside call |
| datetimes | naive UTC |

## Adding records

Add an entry to the matching list in `demo_data.py` (records refer to each other by
`key`, users by email), then run the seeder with `--reset`.
