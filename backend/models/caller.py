from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from core.models.base import Base
from core.models.models import BaseMixin


class Caller(BaseMixin, Base):
    __tablename__ = "callers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    customers = relationship("Customer", back_populates="caller")
