# Planning Guide

**Load: before starting a new feature, task, or architectural decision**

## Before you code

1. Read the relevant pattern docs first — don't invent patterns already defined in `docs/`.
2. Find existing similar code — search for it before writing from scratch.
3. Confirm scope — only build what was asked. No extra features, no speculative abstractions.

## Approaching a task

- **Understand before suggesting.** Read the files involved before proposing changes.
- **Prefer editing over creating.** Only create new files when clearly necessary.
- **Small tasks first.** If a feature has multiple steps, identify the order and start with the smallest safe unit.
- **Check for existing patterns.** Use code search to find how similar things are already done.

## Sub-agents

Use sub-agents for jobs that:
- Are self-contained and don't need full conversation context
- Involve heavy search/exploration that would pollute the main context
- Can run in parallel with other work

Don't spawn sub-agents for simple searches or edits — use tools directly.

## Pre-implementation checklist

- [ ] Relevant docs read (`PATTERNS_CRUD.md`, `IMPORTS.md`, etc.)
- [ ] Existing similar code found and understood
- [ ] Model/router/template structure clear (see `ADDING_ENTITY.md`)
- [ ] Scope agreed — no additions beyond what was asked

## Adding to the project

| Task | Read first |
|------|-----------|
| New entity | `ADDING_ENTITY.md`, `IMPORTS.md` |
| New vertical | `PATTERNS_ADVANCED.md` |
| Auth/session changes | `PATTERNS_AUTH.md`, `IMPORTS.md` |
| Filter or list feature | `PATTERNS_CRUD.md`, `docs/filters.py.md` |
| DB model change | `MODELS.md` (no migrations — recreate DB) |
