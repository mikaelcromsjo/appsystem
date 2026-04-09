# Data Models

## Master DB (multi-tenancy layer)

```
GlobalUser ──< UserTenant >── Tenant
GlobalUser ──< LoginToken
```

| Model | Table | Notes |
|-------|-------|-------|
| `GlobalUser` | global_users | login identity (email + password), shared across tenants |
| `Tenant` | tenants | per-tenant slug, db_url, require_2fa flag |
| `UserTenant` | user_tenants | M2M: GlobalUser ↔ Tenant |
| `LoginToken` | login_tokens | one-time 2FA token; consumed on first use |

These live in `MASTER_DATABASE_URL`. Never import from tenant models into `master.py`.

## Tenant DB (per-tenant data)

```
Account ──< Team ──< Customer ──< Call
                              └─< Alarm
                              └─< ProductCustomer >─ Product
                              └─< Invoice (via Company)

User >── Team (optional, links local user to a team/agent identity)
User.global_user_id → GlobalUser.id  (no FK across DBs; soft reference)

Tag ──< TagLink (polymorphic: object_id + object_type string)
```

## Entity Summary

| Model | Table | Key relations |
|-------|-------|---------------|
| `Account` | accounts | groups Teams |
| `Team` | callers | belongs to Account; has many Customers |
| `Customer` | customers | belongs to Team; has Calls, Alarms, ProductCustomers |
| `Call` | calls | belongs to Customer + Team |
| `Alarm` | alarms | belongs to Customer + Team; optional Product |
| `Product` | products | has many ProductCustomers |
| `ProductCustomer` | product_customers | M2M: Customer ↔ Product, with status |
| `Company` | companies | has many Invoices |
| `Invoice` | invoices | belongs to Company; optional Team (caller_id) |
| `User` | users | optional Team link; `global_user_id` soft-refs GlobalUser |
| `Tag` | tags | linked via TagLink |
| `TagLink` | tag_links | polymorphic: (object_id, object_type) |

## Key field conventions

- `extra` — `MutableDict JSON` on every model; use for extensible fields without migrations
- `status` — `Integer` on Call (call outcome) and ProductCustomer (attendance state)
- `caller_id` — FK on Customer, Call, Alarm, User, Invoice pointing to `callers` (Team) table
- `global_user_id` — on User; soft cross-DB reference to `master.global_users.id`
- `filter_a…filter_h` — 8 boolean columns on Customer (legacy; prefer `extra` for new fields)
- `type_a…type_h` — 8 boolean columns on Product (legacy; prefer `extra` for new fields)

## ProductCustomer status values

`0` no input · `1` not going · `2` maybe · `3` going · `4` paid · `5` attended
