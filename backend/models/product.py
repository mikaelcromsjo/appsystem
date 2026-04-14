from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel
from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.ext.mutable import MutableDict

from core.models.base import Base
from models.base import BaseMixin


class Product(BaseMixin, Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    type_id = Column(String, nullable=False, default="p1")
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    is_filter_1 = Column(Boolean, default=False)
    is_filter_2 = Column(Boolean, default=False)
    is_filter_3 = Column(Boolean, default=False)
    is_filter_4 = Column(Boolean, default=False)
    is_filter_5 = Column(Boolean, default=False)
    is_filter_6 = Column(Boolean, default=False)
    is_filter_7 = Column(Boolean, default=False)
    is_filter_8 = Column(Boolean, default=False)

    extra_visilble_all = Column(Boolean, default=False)

    extra = Column(MutableDict.as_mutable(JSON), default=dict)


class ProductUpdate(BaseModel):
    name: str
    price: Optional[int] = None
    description: Optional[str] = None
    type_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    is_filter_1: bool = False
    is_filter_2: bool = False
    is_filter_3: bool = False
    is_filter_4: bool = False
    is_filter_5: bool = False
    is_filter_6: bool = False
    is_filter_7: bool = False
    is_filter_8: bool = False

    extra_visilble_all: bool = False
    extra: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
