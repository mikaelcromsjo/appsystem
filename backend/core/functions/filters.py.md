# filters.py

Builds a list of SQLAlchemy filter expressions from a flat form dict.

## build_filters(data, model) → list

```python
filters = build_filters(request.session.get("filters", {}), Customer)
```

Returns a mixed list:
- SQLAlchemy filter expressions → pass directly to `.filter(*filters)`
- `{"exact_vals": [...], "column": "field"}` dicts → Python-side exact match

```python
sql_filters = [f for f in filters if not isinstance(f, dict)]
exact_filters = [f for f in filters if isinstance(f, dict)]
rows = query.filter(*sql_filters).all()
# then apply exact_filters in Python
```

## Filter type control

Add `<field>_type` key to the form data to control match behavior:

| `_type` value | Behavior |
|---|---|
| `like` (default) | case-insensitive LIKE `%value%` |
| `exact` | == |
| `has` | OR contains any value |
| `has-all` | AND contains all values |
| `has-not` | AND does NOT contain |

## Column type handling

| Column type | Notes |
|---|---|
| Boolean | `"true"/"false"` strings → Python bool; False includes NULL |
| Integer | Accepts list; cleaned to ints |
| String | LIKE or exact match |
| JSON/JSONB | CSV-style `LIKE` matching + JSON array text matching |
| ARRAY | `.any()` based filters (Postgres only) |
| Date/DateTime | Dict with `"start"`/`"end"` keys for range |
