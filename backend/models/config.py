from sqlalchemy import Column, Text

from core.models.base import Base
from models.base import BaseMixin


class TenantConfig(BaseMixin, Base):
    """Per-tenant key/value config store. value is always a JSON string."""
    __tablename__ = "config"

    key = Column(Text, primary_key=True)
    value = Column(Text, nullable=False)
