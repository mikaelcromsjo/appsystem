from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from core.models.base import Base
from models.base import BaseMixin


class Call(BaseMixin, Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    team = relationship("Team")
    call_date = Column(DateTime, nullable=False)
    status = Column(JSON, default=[])
    note = Column(String, nullable=False)
    extra = Column(MutableDict.as_mutable(JSON), default=dict)


class CallUpdate(BaseModel):
    id: Optional[str] = None
    customer_id: int
    call_date: Optional[datetime] = None
    status: int
    note: str = ""
    extra: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
