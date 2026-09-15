# Claude Code — Project AI Instructions


Make propper test data, all records filled with fake data that looka real. 2 tenatns, 6 users, 2 teams, one user admin of each team. One team has acces to the finansial aspect, the other the call center (both customers). 

Add user to caller, add customers to callers.  create 10 test customers. Connect 8 customers to caller and leave 2 unassigned.
   
Fill at least 4 records of all tables with some type of user editable record, organisations, accounts, invoices, alarms, add customers to caller. calls of to customers (that that caller acces to) with different types with notes and selections connected to products. 6 products with different types. Fill all data that is needed for each record. Look at the edit.html to find fields to use (including extra field). 


**CRM web app** — call center workflow, customer/product management, alarm reminders.

**Stack:** FastAPI · Jinja2 + HTMX + Alpine.js · TailwindCSS (CDN) · SQLite/Postgres

## Start here

Load at the beginning of every session:
- `docs/STRUCTURE.md` — full directory map
- `docs/IMPORTS.md` — layered import rules
- `docs/PATTERNS_CRUD.md` — CRUD, HTMX, filters, rows/reload
- `docs/PATTERNS_AUTH.md` — multi-tenant auth, 2FA

Load when relevant:
- `docs/MODELS.md` — entity relationships, field conventions
- `docs/CONFIG.md` — environment variables reference
- `docs/DOCS.md` — **full documentation index with load hints**
- `docs/TEST_DATA.md` — test data generator, available test users & records for testing

## Role-based guides

- [docs/CLAUDE_PLANNING.md](docs/CLAUDE_PLANNING.md) — task approach, pre-impl checklist, sub-agents
- [docs/CLAUDE_IMPLEMENTING.md](docs/CLAUDE_IMPLEMENTING.md) — code style, Python/Jinja rules, doc policy
- [docs/CLAUDE_DEBUGGING.md](docs/CLAUDE_DEBUGGING.md) — debugging approach, error investigation
- [docs/CLAUDE_REFERENCE.md](docs/CLAUDE_REFERENCE.md) — stack info, database policy

## Code search

`.claude-search/search.py` routes to ripgrep or ast-grep. Use instead of grep/rg directly.
Python results include enclosing function/class context automatically.

**Routing:**
- `name()` or `@decorator` → ast-grep (structural, Python only)
- everything else → ripgrep (text/regex, all files)
- `ast:` prefix → force ast-grep | `text:` prefix → force ripgrep

### ast-grep — structural queries (Python only)

ast-grep matches code structure, not text. Metavariables: `$VAR` = one node, `$$$` = any number of nodes.

**Auto-detected** when query starts with `name(` or `@`. **Method chains require `ast:` prefix** (e.g. `db.query`, `request.session`).

```bash
# Find all calls to a function (any args) — auto-detected
python .claude-search/search.py "build_filters($$$)"
python .claude-search/search.py "populate($$$)"
python .claude-search/search.py "Depends($$$)"

# Find calls with a specific first arg — auto-detected
python .claude-search/search.py "render($VAR, $$$)"

# Find all route decorators — auto-detected
python .claude-search/search.py "@router.get($$$)"
python .claude-search/search.py "@router.post($$$)"

# Method chains — must use ast: prefix
python .claude-search/search.py "ast:db.query($VAR)"
python .claude-search/search.py "ast:request.session.get($$$)"
python .claude-search/search.py "ast:response.headers[$VAR]"
```

### ripgrep — text & regex (all files including templates)

```bash
# Case-insensitive text search
python .claude-search/search.py "customer_filters" -i

# Show 2 lines of context around matches
python .claude-search/search.py "HX-Trigger" -C 2

# Search only Python files
python .claude-search/search.py "get_current_user" --type py

# Search only HTML templates
python .claude-search/search.py "hx-get" --glob "*.html"

# Regex: find all HX-Trigger response headers
python .claude-search/search.py "HX-Trigger.*Reload"

# Search in a specific directory
python .claude-search/search.py "filter_a" backend/models/
```
