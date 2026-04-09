from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from core.models.base import Base
from models.base import BaseMixin


class InvoiceNumber(BaseMixin, Base):
    __tablename__ = "invoice_numbers"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)


class Invoice(BaseMixin, Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, nullable=True)
    caller_id = Column(Integer, ForeignKey("callers.id"), nullable=True)
    caller = relationship("Team")
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    company = relationship("Company")
    date = Column(DateTime, nullable=True)
    extra = Column(MutableDict.as_mutable(JSON), default=dict)


class InvoiceUpdate(BaseModel):
    number: Optional[int] = None
    caller_id: Optional[int] = None
    company_id: Optional[int] = None
    date: Optional[datetime] = None
    extra: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
