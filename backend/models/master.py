from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base

from models.user import pwd_context

MasterBase = declarative_base()


class GlobalUser(MasterBase):
    __tablename__ = "global_users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)   # login identity, globally unique
    password_hash = Column(String, nullable=False)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)

    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)


class Tenant(MasterBase):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    db_url = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    require_2fa = Column(Boolean, default=True)  # if True: send one-time login link after password


class UserTenant(MasterBase):
    __tablename__ = "user_tenants"

    global_user_id = Column(Integer, ForeignKey("global_users.id"), primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), primary_key=True)


class LoginToken(MasterBase):
    """One-time token for 2FA email verification. Consumed on first use."""
    __tablename__ = "login_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, nullable=False, index=True)
    global_user_id = Column(Integer, ForeignKey("global_users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)

    @property
    def is_valid(self) -> bool:
        expires = self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else self.expires_at
        return not self.used and datetime.now(timezone.utc) < expires
