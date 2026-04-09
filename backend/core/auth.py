from fastapi import FastAPI, Request
from fastapi import FastAPI, Request, Depends, HTTPException

from sqlalchemy.orm import relationship, Session
from fastapi import FastAPI, Request, Form, Depends, HTTPException

from core.models.models import User
from core.models.models import BaseMixin, Update, User
from core.database import get_db


# --- Helper ---
def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user")

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_superadmin(request: Request):
    """Dependency for routes that require global superadmin access.
    Reads the is_superadmin flag written to session at login — no DB query needed."""
    if not request.session.get("is_superadmin"):
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return request.session.get("global_user_id")