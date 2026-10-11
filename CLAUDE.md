# Claude Code — Project AI Instructions

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

## Dev knowledge (verified against the running app, 2026-10)

**Runtime**
- Container `appsystem`, port 8070, public at https://system.ia-ai.se. `backend/` is bind-mounted and uvicorn runs with `--reload`: saving any file under `backend/` restarts the app and re-runs startup (schema create, admin init, demo seed).
- Databases live in the Docker volume at `/dbdata`: `master.db` (logins, tenants), `app.db` (tenant `default`), `<slug>.db` per extra tenant. Inspect with `docker exec -i appsystem python - <<'PY'` (`-i` is needed for stdin).
- The session cookie is `https_only`: scripted logins against `http://localhost:8070` silently lose the session. Test against the https URL.
- Routes that use `render()` return the full page shell unless the request has the header `HX-Request: true`.
- Upsert endpoints take JSON (htmx `json-enc`), with extras as flat keys: `"extra.<key>": value`.
- Run git as `devuser` (`runuser -u devuser -- git …`); as root it fails with "dubious ownership".

**Auth and access**
- Login is by email (`<input type="email">`); `GlobalUser` (master DB) holds the password, `User` (tenant DB) is linked by `global_user_id`, and `User.username` is the email.
- One tenant → straight in; several → tenant picker. `Tenant.require_2fa` defaults to True and then emails a login link — it only works with SMTP configured.
- `user.admin = 1` is tenant-wide and bypasses everything. Role bitmasks exist only for `customers`, `products`, `companies`, `invoices` and gate only some writes.
- Every vertical tab is shown to every user (only `admin_only` / `superadmin_only` hide). `Tenant.enabled_verticals` is stored but not enforced.

**What each list shows (non-admin)**
| Tab | Filter |
|---|---|
| Customers | `Customer.assigned_user_id == user.id` |
| Call Center | `Customer.team_id == user.team_id` |
| Companies, Invoices | `team_id == user.team_id` |
| Alarms | `team_id == user.team_id` (admins too) and `date >= today` by default |
| Products | `end_date >= now - 5 days` — a product without `end_date` never lists |
| Accounts | everything |

**Data shapes the templates depend on**
- `Call.status`: plain integer in a JSON column (`1` answer, `2` no answer, `3` outside). A list breaks the row colouring.
- `ProductCustomer.status`: `1` interested, `2` not interested, `3` coming. `type_status` is an integer, so CMS product-type item ids must be numeric strings (`"4"`…`"7"`; totals exist for `s1`–`s7`).
- CMS organisation and personality ids must be integers (templates look them up as ints). `data/cms-config-default.json` uses string ids, so with it those fields do not render.
- `Invoice`: `extra.status` is a string (`"1"` processing, `"2"` OK, `"3"` cancelled) and must be set — the row template emits broken JS without it. `date` is required. `number` comes from the `InvoiceNumber` autoincrement when status becomes `"2"`. Rows: `extra.row = {"1": {description, price, qty}}`.
- Invoice sender = the invoice's team: `team.name` plus address/VAT/bank fields in `team.extra`. `Company.extra.company_name` is what lists and PDFs show.
- Invoice PDFs are written to `backend/pdfs/invoice_<id>.pdf` (tracked in git, not tenant-scoped) and regenerated on each PDF request.
- Bool extras are stored as the string `"true"`; the JSON filter matches that, not JSON `true`.
- Datetimes are naive UTC in the DB; show them with the `| date` filter (Europe/Stockholm).

**Other**
- CMS config is per tenant: table `config`, key `cms`. The global default is in `master.global_config`; new tenants copy it.
- The `| t` filter adds unknown strings to `backend/core/lang/lang_sv.json` at runtime, so that tracked file gets modified just by rendering new labels.
- The alarm scheduler only reads the default tenant DB and delivers over websocket.
- Demo data: `backend/scripts/demo_data.py` + `generate_test_data.py --reset`; see `docs/TEST_DATA.md`.

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
