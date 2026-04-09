# TODO — Refactor for AI-extensibility


## Remaining (future)

- [ ] `filter_a…filter_h` on `Customer` — replace with `extra` JSON (requires DB migration)
- [ ] `type_a…type_h` on `Product` — same

Make sure that the filter and type is indexable. Index on json for fast filtering.

(it is the same and should have the same names we filter types. so filter should also be named type).

- [ ] Move `functions/` domain logic closer to routers or merge hierarchy

- Create a 2 step verification using email
Each tenant has this option. If on then send a login link with token by mail.


- See if we can improve the prototyping system by making things more modular. 

