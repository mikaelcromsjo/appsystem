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

    # Auto-assign default team if user doesn't have one
    if not user.team_id:
        from models.team import Team
        default_team = db.query(Team).filter_by(name="Admin").first()
        if default_team:
            user.team_id = default_team.id
            db.commit()

    return user


def get_current_superadmin(request: Request):
    """Dependency for routes that require global superadmin access.
    Reads the is_superadmin flag written to session at login — no DB query needed."""
    if not request.session.get("is_superadmin"):
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return request.session.get("global_user_id")


def require_vertical_role(vertical_slug: str, role_bit: int):
    """
    Factory for per-vertical role-based access control.

    Returns a FastAPI dependency that checks if the current user has the required
    role in the specified vertical. Tenant admins (user.admin=1) bypass all checks.

    Args:
        vertical_slug: e.g. "invoices", "products"
        role_bit: bitmask integer, e.g. 0b0001 for ADMIN role

    Example:
        @router.post("/invoices/create")
        def create_invoice(..., user=Depends(require_vertical_role("invoices", ADMIN))):
            ...
    """
    def _dependency(user=Depends(get_current_user)):
        from core.roles import user_has_role
        if not user_has_role(user, vertical_slug, role_bit):
            raise HTTPException(status_code=403, detail="Access denied")
        return user
    return _dependency