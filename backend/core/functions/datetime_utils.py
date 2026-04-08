from datetime import datetime
from zoneinfo import ZoneInfo

import data.constants as constants


def local_to_utc(datetime_local_str: str, tz_name: str = constants.DEFAULT_TZ) -> datetime:
    """Convert a datetime-local string (YYYY-MM-DDTHH:MM) from user's timezone to UTC."""
    try:
        if "T" in datetime_local_str:
            naive_dt = datetime.strptime(datetime_local_str, "%Y-%m-%dT%H:%M")
        else:
            naive_dt = datetime.strptime(datetime_local_str, "%Y-%m-%d")
        local_dt = naive_dt.replace(tzinfo=ZoneInfo(tz_name))
        return local_dt.astimezone(ZoneInfo("UTC"))
    except Exception as e:
        raise ValueError(f"Invalid datetime-local format: {datetime_local_str}") from e


def utc_to_local(dt, fmt: str = "%Y-%m-%d %H:%M", tz_name: str = constants.DEFAULT_TZ) -> str:
    """Convert a UTC datetime or ISO string to user's local timezone string."""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            dt = datetime.now(tz=ZoneInfo("UTC"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(ZoneInfo(tz_name)).strftime(fmt)
