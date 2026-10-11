# calls/router.py

Call center tab, mobile call mode (`/calls/number`) and the websocket.

## Websocket

```
GET /get-ws-token          → short-lived JWT (ACCESS_TOKEN_EXPIRE_MINUTES)
WS  /calls/ws?token=<jwt>  → validated, stored in state.active_connections[user_id]
```

- `state.active_connections`: user id (string) → list of sockets. In memory, per process.
- `state.user_data[user_id]` is the last payload for that user; it is sent on
  connect and again whenever the user selects a customer in the call center
  (`GET /calls/customer_data`). Call mode on the phone listens for it to show the
  customer and the `tel:` link.
- `scheduler.py` pushes alarms over the same sockets, to every user of the alarm's team.

## Payloads

```json
{"user_id": "…", "type": "customer_info", "name": "First Last", "number": "…"}
{"type": "alarm", "customer": "First Last", "note": "…", "date": "<iso>"}
```

## Traps

- `routers/teams.py` is mounted under the `/calls` prefix by this vertical's manifest.
- Saving a call requires `user.team_id`.
- `active_connections` / `user_data` are keyed by the user id as a **string**
  (JWT `sub`). An int key silently misses the user's sockets.
