# Data Models

## Relationships

```
Caller ──< Customer ──< Call
                    └─< Alarm
                    └─< ProductCustomer >─ Product
                    └─< Invoice (via Company)

User >── Caller (optional, links user to a call center agent)

Tag ──< TagLink (polymorphic: object_id + object_type string)
```

## Entity Summary

| Model | Table | Key relations |
|-------|-------|---------------|
| `Caller` | callers | has many Customers |
| `Customer` | customers | belongs to Caller; has Calls, Alarms, ProductCustomers |
| `Call` | calls | belongs to Customer + Caller |
| `Alarm` | alarms | belongs to Customer + Caller; optional Product |
| `Product` | products | has many ProductCustomers |
| `ProductCustomer` | product_customers | M2M: Customer ↔ Product, with status |
| `Company` | companies | has many Invoices |
| `Invoice` | invoices | belongs to Company |
| `User` | users | optional Caller link (agent identity) |
| `Tag` | tags | linked via TagLink |
| `TagLink` | tag_links | polymorphic: (object_id, object_type) |

## Key field conventions

- `extra` — `MutableDict JSON` on every model; use for extensible fields without migrations
- `status` — `Integer` on Call (call outcome) and ProductCustomer (attendance state)
- `caller_id` — FK used on Customer, Call, Alarm, User to link to agent
- `filter_a…filter_h` — 8 boolean columns on Customer (legacy; prefer `extra` for new fields)
- `type_a…type_h` — 8 boolean columns on Product (legacy; prefer `extra` for new fields)

## ProductCustomer status values

`0` no input · `1` not going · `2` maybe · `3` going · `4` paid · `5` attended
