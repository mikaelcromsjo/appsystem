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

## Code search

`.claude-search/search.py` routes a query to ripgrep (text, all files) or ast-grep (Python structure). **Neither tool is installed on this host or in the container (2026-10), so the script fails — use `grep -rn` until they are.** The host has `python3`, not `python`.

With the tools installed:

```bash
python3 .claude-search/search.py "build_filters($$$)"        # name( or @decorator → ast-grep
python3 .claude-search/search.py "ast:db.query($VAR)"        # method chains need the ast: prefix
python3 .claude-search/search.py "HX-Trigger" -C 2           # everything else → ripgrep
python3 .claude-search/search.py "hx-get" --glob "*.html"
python3 .claude-search/search.py "filter_a" backend/models/
```

ast-grep metavariables: `$VAR` = one node, `$$$` = any number of nodes. `text:` forces ripgrep.
