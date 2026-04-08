import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.models.base import Base

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_admin_user():
    from core.models.models import User  # lazy: avoids circular import at module level
    db: Session = SessionLocal()
    admin = db.query(User).filter_by(username="admin").first()
    if not admin:
        admin = User(username="admin", admin=1)
        admin.set_password("1234")
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("✅ Default admin user created: admin / changeme")
    db.close()
