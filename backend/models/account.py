from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from core.models.base import Base
from models.base import BaseMixin


class Account(BaseMixin, Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    extra = Column(MutableDict.as_mutable(JSON), default=dict)


class AccountUpdate(BaseModel):
    id: Optional[int] = Field(None, alias="id")
    name: str = Field(..., alias="name")
    extra: Optional[Dict[str, Any]] = Field(None, alias="extra")

    class Config:
        from_attributes = True
