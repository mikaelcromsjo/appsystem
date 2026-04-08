from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel
from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.ext.mutable import MutableDict

from core.models.base import Base
from core.models.models import BaseMixin


class Product(BaseMixin, Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    type_id = Column(String, nullable=False, default="p1")
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    type_a = Column(Boolean, default=False)
    type_b = Column(Boolean, default=False)
    type_c = Column(Boolean, default=False)
    type_d = Column(Boolean, default=False)
    type_e = Column(Boolean, default=False)
    type_f = Column(Boolean, default=False)
    type_g = Column(Boolean, default=False)
    type_h = Column(Boolean, default=False)

    extra_external = Column(Boolean, default=False)
    extra_non_political = Column(Boolean, default=False)
    extra_visilble_all = Column(Boolean, default=False)

    extra = Column(MutableDict.as_mutable(JSON), default=dict)


class ProductUpdate(BaseModel):
    name: str
    price: Optional[int] = None
    description: Optional[str] = None
    type_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    type_a: bool = False
    type_b: bool = False
    type_c: bool = False
    type_d: bool = False
    type_e: bool = False
    type_f: bool = False
    type_g: bool = False
    type_h: bool = False

    extra_external: bool = False
    extra_non_political: bool = False
    extra_visilble_all: bool = False
    extra: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
