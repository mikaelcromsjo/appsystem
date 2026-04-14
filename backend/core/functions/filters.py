import logging

from sqlalchemy import and_, or_, inspect, Boolean, Integer, String, Date, DateTime, JSON
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

logger = logging.getLogger(__name__)


def _build_json_field_filter(model, key: str, value, meta: dict, filter_type: str):
    """Build a filter expression for a key inside the model's `extra` JSON column."""
    col = getattr(model, "extra", None)
    if col is None:
        return None

    json_val = col[key]
    field_type = meta.get("type", "text")

    if field_type == "bool":
        if isinstance(value, str):
            val_bool = value.lower() == "true"
        else:
            val_bool = bool(value)
        as_str = json_val.as_string()
        return as_str == "true" if val_bool else or_(as_str == "false", as_str.is_(None))

    if field_type in ("number", "integer"):
        try:
            int_val = int(value)
        except (ValueError, TypeError):
            return None
        return json_val.as_integer() == int_val

    if field_type == "select":
        vals = value if isinstance(value, list) else [value]
        vals = [v for v in vals if v not in (None, "")]
        if not vals:
            return None
        as_str = json_val.as_string()
        if filter_type == "has":
            return or_(*[as_str == v for v in vals])
        elif filter_type == "has-not":
            return and_(*[as_str != v for v in vals])
        return as_str == vals[0]

    # text / password / date / datetime — ilike or exact
    as_str = json_val.as_string()
    if filter_type == "exact":
        return as_str == value
    return as_str.ilike(f"%{value}%")


def build_filters(data: dict, model, json_fields: dict = None):
    """Build SQLAlchemy filters from form data.

    json_fields: optional dict of {field_key: meta} for extra.* keys,
                 where meta is the extras schema (type, label, …).
    """
    filters = []
    mapper = inspect(model)
    column_types = {col.name: col.type for col in mapper.columns}

    for field, value in data.items():
        if value in (None, "", []):
            continue

        # Handle extra.* JSON sub-fields
        if field.startswith("extra.") and json_fields is not None:
            if value in (None, "", []):
                continue
            key = field[len("extra."):]
            meta = json_fields.get(key)
            if meta is None:
                continue
            filter_type = data.get(f"{field}_type", "like")
            f = _build_json_field_filter(model, key, value, meta, filter_type)
            if f is not None:
                filters.append(f)
            continue

        col = getattr(model, field, None)
        if col is None:
            continue

        col_type = column_types.get(field)
        filter_type = data.get(f"{field}_type", "like")

        if isinstance(col_type, Boolean):
            if isinstance(value, str):
                val_str = value.lower()
                if val_str == "true":
                    val = True
                elif val_str == "false":
                    val = False
                else:
                    continue
            else:
                val = bool(value)
            f = or_(col == False, col.is_(None)) if val is False else col == val
            filters.append(f)
            continue

        if isinstance(col_type, (Date, DateTime)):
            if isinstance(value, dict):
                if "start" in value:
                    filters.append(col >= value["start"])
                if "end" in value:
                    filters.append(col <= value["end"])
            else:
                filters.append(col == value)
            continue

        if isinstance(col_type, Integer):
            vals = value if isinstance(value, list) else [value]
            cleaned_vals = []
            for v in vals:
                if v in (None, "", []):
                    continue
                try:
                    cleaned_vals.append(int(v))
                except (ValueError, TypeError):
                    continue
            if not cleaned_vals:
                continue
            if filter_type == "exact":
                f = col == cleaned_vals[0] if len(cleaned_vals) == 1 else col.in_(cleaned_vals)
            elif filter_type in ("has", "has-all"):
                f = col.in_(cleaned_vals)
            elif filter_type == "has-not":
                f = ~col.in_(cleaned_vals)
            else:
                continue
            filters.append(f)
            continue

        if isinstance(col_type, String):
            vals = value if isinstance(value, list) else [value]
            vals = [str(v) for v in vals if v not in (None, "")]
            if not vals:
                continue
            if filter_type == "exact":
                f = or_(*[col == v for v in vals])
            elif filter_type == "has":
                f = or_(*[col.contains(v) for v in vals])
            elif filter_type == "has-all":
                f = and_(*[col.contains(v) for v in vals])
            elif filter_type == "has-not":
                f = and_(*[~col.contains(v) for v in vals])
            elif filter_type == "like":
                f = col.ilike(f"%{vals[0]}%")
            else:
                continue
            filters.append(f)
            continue

        if isinstance(col_type, ARRAY):
            vals = value if isinstance(value, list) else [value]
            vals = [v for v in vals if v not in (None, "", [])]
            if not vals:
                continue
            if filter_type == "has":
                f = or_(*[col.any(v) for v in vals])
            elif filter_type == "has-all":
                f = and_(*[col.any(v) for v in vals])
            elif filter_type == "has-not":
                f = and_(*[~col.any(v) for v in vals])
            elif filter_type == "exact":
                f = col == vals
            else:
                continue
            filters.append(f)
            continue

        if isinstance(col_type, (JSON, JSONB, String)):
            vals = (
                [v for v in value if v not in (None, "", [])]
                if isinstance(value, list)
                else [v.strip().strip("'\"") for v in value.split(",") if v.strip()]
                if isinstance(value, str)
                else [value]
            )
            if not vals:
                continue
            conditions = []
            for v in vals:
                v_clean = v.strip("'\"")
                csv_cond = or_(
                    col.like(f'"{v_clean},%'), col.like(f'{v_clean},%'),
                    col.like(f'{v_clean}, %'), col.like(f'%,{v_clean},%'),
                    col.like(f'%, {v_clean},%'), col.like(f'%,{v_clean}"'),
                    col.like(f'%, {v_clean}'),
                )
                if isinstance(col_type, (JSON, JSONB)):
                    conditions.append(or_(csv_cond, col.like(f'%"{v_clean}"%')))
                else:
                    conditions.append(csv_cond)

            if filter_type == "has":
                filters.append(or_(*conditions))
            elif filter_type == "has-all":
                filters.append(and_(*conditions))
            elif filter_type == "has-not":
                filters.append(and_(*[~c for c in conditions]))
            elif filter_type == "exact":
                filters.append({"exact_vals": vals, "column": col.key})
            continue

    return filters


def get_exact_vals(filters):
    """Separate SQLAlchemy filters from Python-side exact match filters."""
    exact_filters = [f for f in filters if isinstance(f, dict) and "exact_vals" in f]
    sql_filters = [f for f in filters if not (isinstance(f, dict) and "exact_vals" in f)]
    return sql_filters, exact_filters


def exact_vals(rows, exact_filters):
    """Apply Python-side exact match filtering to rows."""
    results = []
    for row in rows:
        include = True
        for f in exact_filters:
            colname = f["column"]
            expected_vals = set(f["exact_vals"])
            raw_val = getattr(row, colname, None)

            if raw_val is None:
                include = False
                break

            # Normalize actual values (works for CSV or JSON)
            if isinstance(raw_val, list):
                actual_vals = set(str(v) for v in raw_val)
            else:
                actual_vals = set(v.strip() for v in str(raw_val).split(",") if v.strip())

            if actual_vals != expected_vals:
                include = False
                break

        if include:
            results.append(row)
    return results
