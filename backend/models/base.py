from datetime import date, datetime, time, timezone

from pydantic import BaseModel
from sqlalchemy.sql import sqltypes as satypes

try:
    from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, JSONB as PG_JSONB
except Exception:
    PG_ARRAY = tuple()
    PG_JSONB = tuple()


class BaseMixin:
    """Mixin for all ORM models. Provides .empty() and .to_dict()."""
    __empty_overrides__ = {}

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def empty(cls, **overrides):
        """Construct an instance with type-inferred empty values."""
        values = {}
        for col in cls.__table__.columns:
            if col.primary_key:
                continue
            if col.name in overrides:
                values[col.name] = overrides[col.name]
                continue
            t = col.type
            if isinstance(t, (satypes.String, satypes.Text, satypes.Unicode, satypes.UnicodeText)):
                values[col.name] = ""
            elif isinstance(t, satypes.JSON) or (PG_JSONB and isinstance(t, PG_JSONB)):
                values[col.name] = {}
            elif (PG_ARRAY and isinstance(t, PG_ARRAY)) or isinstance(t, satypes.ARRAY):
                values[col.name] = []
            elif isinstance(t, satypes.Boolean):
                values[col.name] = False
            elif isinstance(t, (satypes.Integer, satypes.SmallInteger, satypes.BigInteger)):
                values[col.name] = 0
            elif isinstance(t, (satypes.Numeric, satypes.Float, satypes.DECIMAL)):
                values[col.name] = 0
            elif isinstance(t, satypes.DateTime):
                values[col.name] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
            elif isinstance(t, satypes.Date):
                values[col.name] = date.today()
            elif isinstance(t, satypes.Time):
                values[col.name] = time(0, 0, 0)
            else:
                default = col.default
                if default is not None and getattr(default, "arg", None) is not None \
                        and not callable(getattr(default, "arg", None)):
                    values[col.name] = default.arg
                else:
                    values[col.name] = None
        values.update(getattr(cls, "__empty_overrides__", {}) or {})
        values.update(overrides)
        return cls(**values)


class Update(BaseModel):
    class Config:
        extra = "allow"
