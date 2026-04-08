import logging

from sqlalchemy import and_, or_, inspect, Boolean, Integer, String, Date, DateTime, JSON
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

logger = logging.getLogger(__name__)


def build_filters(data: dict, model):
    """Build SQLAlchemy filters from form data."""
    filters = []
    mapper = inspect(model)
    column_types = {col.name: col.type for col in mapper.columns}

    for field, value in data.items():
        if value in (None, "", []):
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
