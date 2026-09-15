# Authentication & Multi-Tenant Patterns

**Load: always at session start**

## 1. Multi-tenant auth flow

```
POST /login (email + password)
  → verify GlobalUser in master DB
  → if one tenant: store tenant_db_url in session, redirect to dashboard
  → if many tenants: store global_user_id in session, redirect to /pick-tenant
  → if require_2fa: send LoginToken email, redirect to /verify-pending

GET /pick-tenant  →  POST /pick-tenant
  → store tenant_db_url in session, send 2FA email if require_2fa

GET /verify-email?token=<uuid>
  → look up LoginToken in master DB (expires 15 min, single-use)
  → set tenant_db_url in session, clear token, redirect to dashboard
```

Session keys set by auth:
- `tenant_db_url` — resolved tenant DB URL; required by `get_db()`
- `global_user_id` — temporary, used before tenant is selected

`get_db(request)` raises HTTP 401 if `tenant_db_url` is absent.  
Use `get_master_db()` for routes that touch GlobalUser / Tenant / LoginToken.

## 2. WebSocket flow

```
Client → GET /get-ws-token → short-lived JWT
Client → WS /calls/ws?token=<jwt>
Server → validates JWT → stores websocket in active_connections[user_id]
scheduler.py → queries due alarms → sends JSON payload to active connections
```
