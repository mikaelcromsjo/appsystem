# Claude Code — Project AI Instructions

**CRM web app** — call center workflow, customer/product management, invoicing, alarm reminders. Multi-tenant.

**Stack:** FastAPI · Jinja2 + HTMX + Alpine.js · TailwindCSS (committed build) · SQLite, one DB per tenant

## Start here

Read [docs/ai/INDEX.md](docs/ai/INDEX.md) and load `docs/ai/ARCHITECTURE.md`. The index says which of the other docs to load for the task:

- `docs/ai/RUNTIME.md` — container, reload, databases, scripted login
- `docs/ai/UI.md` — page shell, HTMX/Alpine contracts, Tailwind build, translations
- `docs/ai/AUTH_ACCESS.md` — login flow, tenants, roles, list visibility
- `docs/ai/DATA.md` — value shapes, CMS config, upsert/filter conventions
- `docs/ai/RULES.md` — working rules, code style, doc policy
- `docs/TEST_DATA.md` — demo tenants and logins

## Traps that cost the most time

- Only `*.py` changes restart the app (container `appsystem`, https://system.ia-ai.se). Templates reload on change; translations do not.
- New Tailwind class → rebuild `tailwind.css` or it does nothing. New `| t` label → add the Swedish value to `lang_sv.json` and restart **before** rendering. Both in `docs/ai/UI.md`.
- Scripted logins must use the https URL (session cookie is `https_only`); send `HX-Request: true` to get a fragment instead of the whole shell.
- No migrations: `create_all()` does not add columns to existing tables. See `docs/ai/ARCHITECTURE.md`.
- `backend/routers/customers.py` is dead code; the live router is `backend/verticals/customers/router.py`.
- Rendering pages modifies tracked files (`lang_sv.json`, `backend/pdfs/`). Check `git status` before committing.
- Run git as `devuser`; as root it fails with "dubious ownership".
- Search with `rg <pattern> .` (host only, in `~/.local/bin`; not in the container). Always give a path: without one `rg` reads stdin and hangs when scripted. `.rgignore` keeps it out of `node_modules`; add `--max-columns 200` when hits land in `tailwind.css`. The host has `python3`, not `python`.
