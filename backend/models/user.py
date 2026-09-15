from typing import Any, Dict, Optional

from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from core.models.base import Base
from models.base import BaseMixin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=True)   # kept for migration; auth is in GlobalUser
    global_user_id = Column(Integer, nullable=True)  # references master.global_users.id (no FK across DBs)
    admin = Column(Integer, default=0)
    roles = Column(MutableDict.as_mutable(JSON), default=dict)  # {"vertical_slug": bitmask}
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    team = relationship("Team")
    extra = Column(MutableDict.as_mutable(JSON), default=dict)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)

    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)


class UserUpdate(BaseModel):
    team_id: Optional[int] = None
    roles: Optional[Dict[str, int]] = None
    extra: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
