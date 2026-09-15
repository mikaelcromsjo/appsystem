# Reference

**Load: when learning about the stack, configuring infrastructure, or understanding design decisions**

## Project overview

**CRM web app** — call center workflow, customer/product management, alarm reminders.

**Stack:** FastAPI · Jinja2 + HTMX + Alpine.js · TailwindCSS (CDN) · SQLite/Postgres

## Database

- Do not use alembic migrations. Instead we recreate new databases when needed.

For multi-tenancy architecture and data models, see [MODELS.md](MODELS.md).
