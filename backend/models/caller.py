from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict

from core.models.base import Base
from models.base import BaseMixin


class Team(BaseMixin, Base):
    __tablename__ = "callers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    account = relationship("Account")
    extra = Column(MutableDict.as_mutable(JSON), default=dict)
    customers = relationship("Customer", back_populates="caller")
