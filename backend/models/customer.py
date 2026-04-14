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
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    description_phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    contributes = Column(Integer, nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    team = relationship("Team", back_populates="customers")
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    comment = Column(String, nullable=True)
    sub_caller = Column(String, nullable=True)
    organisations = Column(JSON, default=[])
    categories = Column(JSON, default=[])
    personality_type = Column(Integer, nullable=True)
    is_filter_1 = Column(Boolean, default=False)
    is_filter_2 = Column(Boolean, default=False)
    is_filter_3 = Column(Boolean, default=False)
    is_filter_4 = Column(Boolean, default=False)
    is_filter_5 = Column(Boolean, default=False)
    is_filter_6 = Column(Boolean, default=False)
    is_filter_7 = Column(Boolean, default=False)
    is_filter_8 = Column(Boolean, default=False)
    is_filter_9 = Column(Boolean, default=False)
    is_filter_10 = Column(Boolean, default=False)
    is_filter_11 = Column(Boolean, default=False)
    is_filter_12 = Column(Boolean, default=False)
    is_filter_13 = Column(Boolean, default=False)
    is_filter_14 = Column(Boolean, default=False)
    is_filter_15 = Column(Boolean, default=False)
    is_filter_16 = Column(Boolean, default=False)
    is_filter_17 = Column(Boolean, default=False)
    is_filter_18 = Column(Boolean, default=False)
    is_filter_19 = Column(Boolean, default=False)
    is_filter_20 = Column(Boolean, default=False)
    is_filter_21 = Column(Boolean, default=False)
    is_filter_22 = Column(Boolean, default=False)
    is_filter_23 = Column(Boolean, default=False)
    is_filter_24 = Column(Boolean, default=False)
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
    assigned_user_id: Optional[int] = None
    is_filter_1: Optional[bool] = False
    is_filter_2: Optional[bool] = False
    is_filter_3: Optional[bool] = False
    is_filter_4: Optional[bool] = False
    is_filter_5: Optional[bool] = False
    is_filter_6: Optional[bool] = False
    is_filter_7: Optional[bool] = False
    is_filter_8: Optional[bool] = False
    categories: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    extra: Optional[Dict[str, Any]] = None

    @field_validator("phone")
    def normalize_phone(cls, v: Optional[str]):
        if v:
            return formatPhoneNr(v)
        return v

    @field_validator("tags", mode="before")
    def parse_tags(cls, v):
        """Accept Tagify JSON string, plain CSV, or list. Always returns clean list of strings."""
        if not v:
            return []

        if isinstance(v, list):
            # Extract values from list items (handles Tagify format with dicts)
            result = []
            for item in v:
                if isinstance(item, dict):
                    tag = item.get("value", "")
                else:
                    tag = str(item).strip()
                if tag:
                    result.append(tag)
            return result

        if isinstance(v, str):
            # Try JSON parsing first
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    result = []
                    for item in parsed:
                        if isinstance(item, dict):
                            tag = item.get("value", "")
                        else:
                            tag = str(item).strip()
                        if tag:
                            result.append(tag)
                    return result
            except (json.JSONDecodeError, ValueError):
                pass

            # Fall back to CSV, but be defensive about malformed strings
            # Remove any common escape characters and quotes
            cleaned = v.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")
            cleaned = cleaned.strip("'\"[]").strip()

            # Split by comma and clean each tag
            if cleaned:
                return [t.strip("'\" ") for t in cleaned.split(",") if t.strip("'\" ")]

        return []
