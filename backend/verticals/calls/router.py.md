# calls.py

Call center workflow router + WebSocket for real-time alarm delivery.

## WebSocket flow

```
GET /get-ws-token          → short-lived JWT (ACCESS_TOKEN_EXPIRE_MINUTES)
WS  /calls/ws?token=<jwt>  → validated, stored in state.active_connections[user_id]
```

- `active_connections: Dict[str, List[WebSocket]]` in `state.py`
- `user_data: Dict[str, dict]` stores per-user state sent on connect
- `scheduler.py` queries due alarms and pushes JSON payloads to open sockets

## Alarm payload shape

```json
{"type": "alarm", "customer": "First Last", "note": "...", "date": "<iso>"}
```

## Key routes

| Method | Path | Returns |
|--------|------|---------|
| GET/POST | `/calls/dashboard` | call center shell — requires `user.team_id` (400 otherwise) |
| GET | `/calls/customers` | customer list fragment |
| GET | `/calls/<id>/calls` | call history for customer |
| GET | `/calls/products` | product list fragment |
| WS | `/calls/ws` | WebSocket endpoint |
