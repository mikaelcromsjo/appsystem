# Implementation Guide

**Load: when writing code, creating features, or refactoring**

## Documentation policy

Compact, AI-optimized. All docs in `docs/` or alongside the file they describe.

Per-file docs (`<file>.py.md`) only for non-obvious files:
- `backend/core/functions/populate.py.md`
- `backend/core/functions/filters.py.md`
- `backend/routers/calls.py.md`

Update the relevant `.py.md` and directory doc after any larger edit.

## Translation

Use filter `{ "English string" | t }` in Jinja — `t` = translation function.

## Python rules

- Wrap f-strings in parentheses for implicit concatenation.
- Prefer **explicit, readable** code over clever tricks.
- Delete or update outdated comments; remove dead code.
- Always use `timezone.utc`

## Jinja2 template rules

- Jinja2 is NOT Python. Unsupported: bitwise `&` `|` `^` `~`, walrus `:=`, list comprehensions, f-strings. Use registered filters for custom operations (e.g. `| bitand(x)`).

## Claude Code (editing)

Use unique, short search strings for precise replacements.
