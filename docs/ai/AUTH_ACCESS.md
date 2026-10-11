# Auth, tenants and access

## Identity

- Login is by email. `GlobalUser` (master DB) holds the password and
  `is_superadmin`. `User` (tenant DB) is the same person inside one tenant, linked
  by `global_user_id`; `User.username` is the email. `User.password_hash` is unused.
- A person needs three rows to log in to a tenant: `GlobalUser`, `UserTenant`
  (master) and `User` (tenant). Missing the last one gives 403 "No local user".
- `user.admin = 1` is tenant-wide. Superadmin is global and only opens the
  Global Admin tab.

## Login flow

`POST /login` → one active tenant: straight in; several: tenant picker; none and
superadmin: Global Admin. If `Tenant.require_2fa` (default **True**) a one-time
link is emailed instead (15 min, single use, `GET /verify-login?token=`); that only
works with SMTP configured, so demo tenants have it off.

Session keys set at login: `user` (tenant `User.id`), `tenant_db_url`,
`tenant_slug`, `global_user_id`, `is_superadmin`, `admin`.

- `get_db()` picks the tenant DB from `session["tenant_db_url"]` and raises 401
  without it; any 401 is turned into a redirect to `/login`.
- `get_current_user()` assigns the `Admin` team to a user without a team, as a
  side effect.
- Use `get_master_db()` for `GlobalUser` / `Tenant` / `LoginToken` / `GlobalConfig`.

## Roles

`User.roles` = `{"<vertical slug>": bitmask}`; bits are defined in
`verticals/<slug>/roles.py` and listed in the manifest's `role_defs` (which is what
the admin UI offers). Check with `user_has_role()` (`core/roles.py`) or the
`require_vertical_role()` dependency; admins pass every check.

Enforcement is thin — do not assume a route is protected:

- Roles exist only for `customers`, `products`, `companies`, `invoices`, and gate
  only a few writes (product save/delete, customer delete).
- Every tab is shown to every user; only `admin_only` / `superadmin_only` hide a
  tab, and that hiding is client side (`x-show`). The server check is in each route.
- `Tenant.enabled_verticals` is stored but not enforced. The env var
  `ENABLED_VERTICALS` is enforced, for the whole process.
- Some routes check nothing beyond a valid tenant session (e.g. account delete).

## What each list shows to a non-admin

| Tab | Filter |
|---|---|
| Customers | `Customer.assigned_user_id == user.id` |
| Call Center | `Customer.team_id == user.team_id` |
| Companies, Invoices | `team_id == user.team_id` |
| Alarms | `team_id == user.team_id` (admins too) and `date >= today` by default |
| Products | `end_date >= now - 5 days` — a product without `end_date` never lists |
| Accounts | everything |

## Websocket

`GET /get-ws-token` → short-lived JWT → `WS /calls/ws?token=`. Connections are
kept per user id in `state.active_connections`. Used for alarm pushes and for
sending the selected customer to the user's phone (call mode).
