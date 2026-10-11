# AI docs — index

Compact notes for AI agents: only what is not obvious from reading the code, and
what breaks silently when you get it wrong. Everything else — file layout, routes,
columns, env defaults — read from the code; it is small (~9k lines of Python).

| Doc | Load when | Contains |
|---|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | always | where code goes, vertical contract, legacy/dead code to avoid, schema policy |
| [RUNTIME.md](RUNTIME.md) | running, testing or debugging the app | container, reload behaviour, databases, scripted login, tooling that is missing |
| [UI.md](UI.md) | touching templates, JS or CSS | page shell, HTMX/Alpine contracts, modal store, reload events, Tailwind build, translations |
| [AUTH_ACCESS.md](AUTH_ACCESS.md) | login, tenants, roles, "why can't user X see Y" | login flow, session keys, role model, what each list filters on |
| [DATA.md](DATA.md) | reading/writing records, seeding, CMS config | value shapes the templates depend on, upsert/populate/filter conventions |
| [RULES.md](RULES.md) | before writing code or docs | working rules, code style, doc policy |

Other docs:

- [../TEST_DATA.md](../TEST_DATA.md) — demo tenants, logins (password `1234`), reseeding.
- [../TEST_SCENARIOS.md](../TEST_SCENARIOS.md) — manual test walkthroughs per role.
- Per-file notes, next to the code: `backend/core/functions/populate.py.md`,
  `backend/core/functions/filters.py.md`, `backend/verticals/calls/router.py.md`.

Where to look instead of a doc:

| Need | Read |
|---|---|
| Env vars and defaults | `backend/core/config.py`, `backend/core/database.py` (DB URLs), `backend/core/loader.py` (`ENABLED_VERTICALS`); deployed values in `docker-compose.yml` |
| Models and relations | `backend/models/*.py` (one file per entity; `master.py` = master DB) |
| A vertical's routes, columns, roles | `backend/verticals/<slug>/` (`__init__.py`, `router.py`, `roles.py`) |
| Markup to copy for a list/modal vertical | `backend/verticals/companies/` (smallest complete example) |
| Markup to copy for an admin sub-page | `backend/verticals/admin/templates/admin/users.html` |
