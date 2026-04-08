from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from core.models.base import Base
from models.base import BaseMixin


class ProductCustomer(BaseMixin, Base):
    __tablename__ = "product_customers"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    customer = relationship("Customer", lazy="joined")
    product = relationship("Product", lazy="joined")
    status = Column(Integer, nullable=False)
    type_status = Column(Integer, nullable=True)
    order_date = Column(DateTime, nullable=True)
    extra = Column(MutableDict.as_mutable(JSON), default=dict)
