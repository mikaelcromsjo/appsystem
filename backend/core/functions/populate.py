from typing import Any, Type, Union, get_args, get_origin
import json

from pydantic import BaseModel


def populate(update_dict: dict, db_obj: Any, pyd_model: Type[BaseModel]) -> Any:
    """Convert a raw dict to a Pydantic model, then populate the DB model."""
    preprocessed = {}

    for field_name, value in update_dict.items():
        field_info = pyd_model.model_fields.get(field_name)
        if not field_info:
            continue

        field_type = field_info.annotation
        origin = get_origin(field_type)
        args = get_args(field_type)

        if origin is Union and type(None) in args:
            base_type = next((a for a in args if a is not type(None)), str)
        else:
            base_type = field_type

        if value == "" and (base_type in (int, float, bool) or (origin is Union and type(None) in args)):
            preprocessed[field_name] = None
            continue

        if base_type == str and isinstance(value, list):
            cleaned = [str(v).strip() for v in value if str(v).strip() != ""]
            preprocessed[field_name] = ",".join(cleaned)
            continue

        if base_type == str and isinstance(value, dict):
            preprocessed[field_name] = json.dumps(value, ensure_ascii=False)
            continue

        if base_type == bool and isinstance(value, list):
            last_val = str(value[-1]).lower().strip()
            preprocessed[field_name] = last_val in ("true", "1", "on", "yes")
            continue

        preprocessed[field_name] = value

    pyd_instance = pyd_model(**preprocessed)
    for field_name, value in pyd_instance.model_dump(exclude_unset=True).items():
        setattr(db_obj, field_name, convert_value_for_field(pyd_instance, field_name, value))
    return db_obj


def convert_value_for_field(pyd_instance: BaseModel, field_name: str, value: Any):
    """Convert value to correct type based on Pydantic field type."""
    import json
    from typing import Union, get_origin, get_args

    field_type = pyd_instance.model_fields[field_name].annotation
    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin is Union and type(None) in args:
        target_type = next((a for a in args if a is not type(None)), str)
        value = _convert_value(target_type, value) if value not in ("", None) else None
    else:
        value = _convert_value(field_type, value)

    if value is not None and (field_type == str or (origin is Union and str in args)):
        if isinstance(value, list):
            value = ",".join(map(str, value))
        elif isinstance(value, dict):
            value = json.dumps(value, ensure_ascii=False)
    return value


def _convert_value(field_type, value):
    """Safe type conversion."""
    import json
    from typing import get_origin

    origin = get_origin(field_type)
    if value is None:
        return None
    if field_type == int:
        return int(value)
    if field_type == float:
        return float(value)
    if field_type == bool:
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)
    if field_type == str:
        if isinstance(value, list):
            return ",".join(map(str, value))
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
    if origin == list:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                return [v.strip() for v in value.split(",") if v.strip()]
        return list(value)
    if origin == dict:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return {}
        return dict(value)
    return value
