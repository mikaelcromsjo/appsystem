from typing import Any, Dict, Optional

from pydantic import BaseModel
from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from core.models.base import Base
from models.base import BaseMixin


class Company(BaseMixin, Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    caller_id = Column(Integer, ForeignKey("callers.id"), nullable=True)
    caller = relationship("Team")
    comment = Column(String, nullable=True)
    extra = Column(MutableDict.as_mutable(JSON), default=dict)


class CompanyUpdate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    comment: Optional[str] = None
    caller: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None
