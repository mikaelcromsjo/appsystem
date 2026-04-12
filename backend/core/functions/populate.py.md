# populate.py

Converts a raw form dict into a typed Pydantic model, then writes fields onto a SQLAlchemy ORM object.

## populate(update_dict, db_obj, pyd_model)

```python
record = populate(data_dict, record, CustomerUpdate)
```

**Pre-processing rules (before Pydantic validation):**
- Empty string + numeric/optional field → `None`
- `list` value + `str` Pydantic field → comma-joined string
- `dict` value + `str` Pydantic field → JSON string
- `list` value + `bool` field → last item coerced to bool

**Important:** pop FK/relationship fields from `data_dict` BEFORE calling populate. Handle them separately after.

```python
team_id = data_dict.pop("team_id", None)
record = populate(data_dict, record, EntityUpdate)
if team_id:
    record.team = db.get(Team, int(team_id))
```

## extra.* convention

Before calling populate, merge `extra.*` prefixed keys:
```python
for key in [k for k in data_dict if k.startswith("extra.")]:
    data_dict.setdefault("extra", {})[key.split(".", 1)[1]] = data_dict.pop(key)
```
