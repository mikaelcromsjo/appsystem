from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from core.models.base import Base
from core.models.models import BaseMixin


class Alarm(BaseMixin, Base):
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    customer = relationship("Customer")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product = relationship("Product")
    caller_id = Column(Integer, ForeignKey("callers.id"), nullable=False)
    caller = relationship("Caller")
    date = Column(DateTime, nullable=False)
    reminder = Column(DateTime, nullable=False)
    reminder_sent = Column(DateTime, nullable=True)
    note = Column(String, nullable=True)
    extra = Column(MutableDict.as_mutable(JSON), default=dict)
