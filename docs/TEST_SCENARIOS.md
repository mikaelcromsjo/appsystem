# Testing Scenarios with the Demo Data

Logins, records and how to reseed are described in [TEST_DATA.md](TEST_DATA.md).
All passwords are `1234`.

## Call center (`sales@nordljus.example`)

1. **Customers** — six customers assigned to Sara. Open Erik Lundgren: category, organisations,
   personality type, tags and three product selections are shown.
2. **Call Center** — eight customers (the whole Kundtjänst team). Select Anders Sjöberg: two
   unanswered calls (red) and today's answered call (green) with notes.
3. Select a product for a customer, set *Coming* and a type status, press *Answer*, write a note.
   A new call appears in the customer's log and the selection is saved.
4. Set an alarm from the call form — it shows up under **Alarms**.
5. **Products** — six products of four types. Open *Höstmingel på Münchenbryggeriet*: three
   customers with their statuses.
6. **Customers → Filter** — filter on category, organisation, interests or the extras
   (*Nyhetsbrev*, *GDPR-samtycke*).
7. **Companies** and **Invoices** are empty for this user (they belong to team Ekonomi).

## Invoicing (`finance@nordljus.example`)

1. **Companies** — five companies. Open Øresund Events ApS: Danish address and org number.
2. **Invoices** — seven invoices: OK (numbered, PDF button), cancelled (PDF with watermark) and
   processing (no number, editable).
3. Open the PDF for invoice 3: EUR, 0 % VAT, sender details from team Ekonomi.
4. Edit a processing invoice, add a row, save.
5. **Accounts** — four accounts with bank details.

## Admin and multi-tenancy (`anna.lindqvist@nordljus.example`)

1. After login the tenant picker lists *Nordljus Media AB* and *Fjällvind Event AB*.
2. In Nordljus: **Customers** lists all ten, including the two unassigned. Select them and use
   *Assign Team* / *Assign User*.
3. **Admin → Users** — six demo users with teams and roles.
4. Log out, log in again and pick Fjällvind: completely different customers, products and
   invoices — nothing from Nordljus is visible.

## Role checks

- `finance@…` has no `products` role: saving a product returns 403.
- Non-admins do not see the Admin tab.
