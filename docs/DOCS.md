# Documentation Index

## AI role-based guides
- [CLAUDE_PLANNING.md](CLAUDE_PLANNING.md) — task approach, pre-impl checklist, sub-agents
- [CLAUDE_IMPLEMENTING.md](CLAUDE_IMPLEMENTING.md) — code style, Python/Jinja rules, doc policy
- [CLAUDE_DEBUGGING.md](CLAUDE_DEBUGGING.md) — debugging approach, error investigation
- [CLAUDE_REFERENCE.md](CLAUDE_REFERENCE.md) — stack info, database policy

## Core (load at session start)
- [STRUCTURE.md](STRUCTURE.md) — full directory map
- [IMPORTS.md](IMPORTS.md) — layered import rules + dependency hierarchy
- [PATTERNS_CRUD.md](PATTERNS_CRUD.md) — CRUD upsert, HTMX render, filters, rows/reload
- [PATTERNS_AUTH.md](PATTERNS_AUTH.md) — multi-tenant login, 2FA, WebSocket auth

## Load when relevant
- [MODELS.md](MODELS.md) — entity relationships, field conventions
- [CONFIG.md](CONFIG.md) — environment variables reference

## UI patterns
- [UI_USER_VERTICALS.md](UI_USER_VERTICALS.md) — tables, rows, search, toolbar, modals, inline edits (customers/products pattern)
- [UI_ADMIN_VERTICALS.md](UI_ADMIN_VERTICALS.md) — dashboard nav, back button, create forms, tables, inline edits (admin pattern)

## Building features
- [PATTERNS_ADVANCED.md](PATTERNS_ADVANCED.md) — polymorphic tags, custom verticals, new verticals
- [ADDING_ENTITY.md](ADDING_ENTITY.md) — step-by-step: create model, router, templates

## Reports & planning
- [REPORT_MODULARITY.md](REPORT_MODULARITY.md) — multi-vertical SaaS modularity, AI codegen, missing infrastructure
- [PLAN_customer_extra_migration.md](PLAN_customer_extra_migration.md) — move code_name, controlled, filter_a–h from columns into customer.extra JSON (5 staged steps)

## Per-file (complex files only)
- [populate.py.md](../backend/core/functions/populate.py.md) — data type conversion + populate() algorithm
- [filters.py.md](../backend/core/functions/filters.py.md) — build_filters() + exact value matching
- [calls.py.md](../backend/routers/calls.py.md) — call routing + WebSocket handler
