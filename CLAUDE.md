# About

CRM web app — call center workflow, customer/product management, alarm reminders.

**Stack:** FastAPI · Jinja2 + HTMX + Alpine.js · TailwindCSS (CDN) · SQLite/Postgres

# Start here

Load at the beginning of every session:
- `docs/PATTERNS.md` — how to build features (CRUD, HTMX, filters, WebSocket)
- `docs/STRUCTURE.md` — full file map + env vars

Load when needed:
- `docs/MODELS.md` — entity relationships
- `docs/IMPORTS.md` — import layer rules
- `docs/DOCS.md` — full doc index

# Documentation

Compact, AI-optimized. All docs in `docs/` or alongside the file they describe.

Per-file docs (`<file>.py.md`) only for non-obvious files:
- `backend/core/functions/populate.py.md`
- `backend/core/functions/filters.py.md`
- `backend/routers/calls.py.md`

Update the relevant `.py.md` and directory doc after any larger edit.

# Claude Code

## Edit files
Use unique, short search strings for precise replacements.

## Sub agents
Use sub agents for small jobs that do not need full context.

# Python rules

- Wrap f-strings in parentheses for implicit concatenation.
- Prefer **explicit, readable** code over clever tricks.
- Delete or update outdated comments; remove dead code.
