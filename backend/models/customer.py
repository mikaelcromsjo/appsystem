import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, field_validator
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from core.models.base import Base
from core.functions.helpers import formatPhoneNr
from models.base import BaseMixin


class Customer(BaseMixin, Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    last_call_date = Column(DateTime, nullable=True)
    code_name = Column(Boolean, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    description_phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    contributes = Column(Integer, nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    team = relationship("Team", back_populates="customers")
    comment = Column(String, nullable=True)
    sub_caller = Column(String, nullable=True)
    organisations = Column(JSON, default=[])
    categories = Column(JSON, default=[])
    personality_type = Column(Integer, nullable=True)
    controlled = Column(Boolean, default=False)
    filter_a = Column(Boolean, default=False)
    filter_b = Column(Boolean, default=False)
    filter_c = Column(Boolean, default=False)
    filter_d = Column(Boolean, default=False)
    filter_e = Column(Boolean, default=False)
    filter_f = Column(Boolean, default=False)
    filter_g = Column(Boolean, default=False)
    filter_h = Column(Boolean, default=False)
    tags = Column(JSON, default=[])
    extra = Column(MutableDict.as_mutable(JSON), default=dict)


class CustomerUpdate(BaseModel):
    first_name: str
    last_name: str
    user_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    comment: Optional[str] = None
    sub_caller: Optional[str] = None
    organisations: Optional[List[str]] = []
    personality_type: Optional[int] = None
    contributes: Optional[int] = None
    team: Optional[int] = None
    controlled: Optional[bool] = False
    filter_a: Optional[bool] = False
    filter_b: Optional[bool] = False
    filter_c: Optional[bool] = False
    filter_d: Optional[bool] = False
    filter_e: Optional[bool] = False
    filter_f: Optional[bool] = False
    filter_g: Optional[bool] = False
    filter_h: Optional[bool] = False
    categories: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    extra: Optional[Dict[str, Any]] = None
    code_name: Optional[bool] = False

    @field_validator("phone")
    def normalize_phone(cls, v: Optional[str]):
        if v:
            return formatPhoneNr(v)
        return v

    @field_validator("tags", mode="before")
    def parse_tags(cls, v):
        """Accept Tagify JSON string, plain CSV, or list."""
        if not v:
            return []
        if isinstance(v, list):
            return [item.get("value", item) if isinstance(item, dict) else item for item in v]
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [item.get("value", item) if isinstance(item, dict) else item for item in parsed]
            except json.JSONDecodeError:
                return [t.strip() for t in v.split(",") if t.strip()]
        return []
