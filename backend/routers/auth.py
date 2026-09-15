import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from jose import jwt
from sqlalchemy.orm import Session

from core.auth import get_current_user
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, JWT_SECRET_KEY
from core.database import get_db, get_master_db
from core.email import send_login_link
from core.i18n import clear_translator_cache, get_best_language_match, get_translator_cached
from core.config import SUPPORTED_LANGUAGES
from core.models.models import User
from models.master import GlobalUser, LoginToken, Tenant, UserTenant
from templates import templates

router = APIRouter()


@router.get("/favicon.ico")
def favicon():
    favicon_path = "core/static/favicon.ico"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return Response(status_code=204)


@router.get("/login")
async def login_get(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})


@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    master_db: Session = Depends(get_master_db),
):
    lang_code = request.cookies.get("lang_code")
    if not lang_code:
        accept_language = request.headers.get("accept-language", "")
        lang_code = get_best_language_match(accept_language, SUPPORTED_LANGUAGES)

    global_user = master_db.query(GlobalUser).filter_by(email=email).first()
    if not global_user or not global_user.verify_password(password):
        return templates.TemplateResponse(
            request, "login.html", {"request": request, "error": "Invalid credentials"}
        )

    request.session["global_user_id"] = global_user.id
    request.session["is_superadmin"] = bool(global_user.is_superadmin)

    tenants = (
        master_db.query(Tenant)
        .join(UserTenant, Tenant.id == UserTenant.tenant_id)
        .filter(UserTenant.global_user_id == global_user.id, Tenant.active == True)
        .all()
    )

    if len(tenants) == 1:
        return await _activate_tenant(request, master_db, global_user.id, tenants[0])

    if not tenants and global_user.is_superadmin:
        return RedirectResponse(url="/global-admin/", status_code=303)

    # Multiple tenants — show picker
    return templates.TemplateResponse(
        request, "pick_tenant.html", {"request": request, "tenants": tenants}
    )


@router.post("/pick-tenant")
async def pick_tenant(
    request: Request,
    tenant_id: int = Form(...),
    master_db: Session = Depends(get_master_db),
):
    global_user_id = request.session.get("global_user_id")
    if not global_user_id:
        return RedirectResponse(url="/login", status_code=303)

    tenant = (
        master_db.query(Tenant)
        .join(UserTenant, Tenant.id == UserTenant.tenant_id)
        .filter(
            Tenant.id == tenant_id,
            UserTenant.global_user_id == global_user_id,
            Tenant.active == True,
        )
        .first()
    )
    if not tenant:
        raise HTTPException(status_code=403, detail="Access denied")

    return await _activate_tenant(request, master_db, global_user_id, tenant)


async def _activate_tenant(request: Request, master_db: Session, global_user_id: int, tenant: Tenant):
    """Complete login for a tenant. If require_2fa, send a one-time link instead."""
    if tenant.require_2fa:
        return await _send_2fa_link(request, master_db, global_user_id, tenant)
    return await _complete_login(request, master_db, global_user_id, tenant)


async def _send_2fa_link(request: Request, master_db: Session, global_user_id: int, tenant: Tenant):
    """Issue a one-time token, email it, show the waiting page."""
    global_user = master_db.query(GlobalUser).filter_by(id=global_user_id).first()

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    master_db.add(LoginToken(
        token=token,
        global_user_id=global_user_id,
        tenant_id=tenant.id,
        expires_at=expires_at,
    ))
    master_db.commit()

    send_login_link(global_user.email, token)

    return templates.TemplateResponse(
        request, "verify_pending.html",
        {"request": request, "email": global_user.email},
    )


async def _complete_login(request: Request, master_db: Session, global_user_id: int, tenant: Tenant):
    """Set session and redirect to dashboard."""
    from core.database import _get_tenant_engine
    from core.models.base import Base
    from sqlalchemy.orm import sessionmaker

    # Import all models to register them with Base.metadata before create_all
    import models.account, models.alarm, models.call, models.company  # noqa: F401
    import models.customer, models.invoice, models.product, models.product_customer  # noqa: F401
    import models.tag, models.team  # noqa: F401

    tenant_engine = _get_tenant_engine(tenant.db_url)
    # Ensure schema exists (safe on existing DBs — create_all is idempotent)
    Base.metadata.create_all(bind=tenant_engine)

    tenant_db = sessionmaker(bind=tenant_engine)()
    try:
        local_user = tenant_db.query(User).filter_by(global_user_id=global_user_id).first()
        if not local_user:
            raise HTTPException(status_code=403, detail="No local user for this tenant")
        global_user = master_db.query(GlobalUser).filter_by(id=global_user_id).first()
        request.session["authenticated"] = True
        request.session["admin"] = local_user.admin
        request.session["user"] = local_user.id
        request.session["tenant_slug"] = tenant.slug
        request.session["tenant_db_url"] = tenant.db_url
        request.session["global_user_id"] = global_user_id
        request.session["is_superadmin"] = bool(global_user and global_user.is_superadmin)
    finally:
        tenant_db.close()

    return RedirectResponse(url="/", status_code=303)


@router.get("/verify-login")
async def verify_login(request: Request, token: str, master_db: Session = Depends(get_master_db)):
    """Consume a one-time login token from the email link."""
    login_token = master_db.query(LoginToken).filter_by(token=token).first()

    if not login_token or not login_token.is_valid:
        return templates.TemplateResponse(
            request, "login.html",
            {"request": request, "error": "This link is invalid or has expired. Please log in again."},
        )

    login_token.used = True
    master_db.commit()

    tenant = master_db.query(Tenant).filter_by(id=login_token.tenant_id).first()
    return await _complete_login(request, master_db, login_token.global_user_id, tenant)


@router.get("/logout")
@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    clear_translator_cache()
    return templates.TemplateResponse(
        request, "login.html", {"request": request, "message": "Logged out"}
    )


@router.get("/get-ws-token")
def get_ws_token(request: Request):
    user = str(request.session.get("user"))
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = jwt.encode({"sub": user, "exp": expire}, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return {"ws_token": token}


@router.post("/users/create")
async def create_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    team_id: int = Form(None),
    db: Session = Depends(get_db),
    master_db: Session = Depends(get_master_db),
):
    current_user = get_current_user(request, db)
    if not current_user.admin:
        raise HTTPException(status_code=403, detail="Only admins can create users")

    # Create GlobalUser for auth
    global_user = GlobalUser(email=email)
    global_user.set_password(password)
    master_db.add(global_user)
    master_db.flush()

    # Link to current tenant
    tenant_slug = request.session.get("tenant_slug")
    tenant = master_db.query(Tenant).filter_by(slug=tenant_slug).first()
    if tenant:
        master_db.add(UserTenant(global_user_id=global_user.id, tenant_id=tenant.id))
    master_db.commit()

    # Create local User in tenant DB
    # If no team_id provided, assign to default "Admin" team
    if not team_id:
        from models.team import Team
        default_team = db.query(Team).filter_by(name="Admin").first()
        if default_team:
            team_id = default_team.id

    new_user = User(username=email, team_id=team_id, global_user_id=global_user.id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"User {email} created successfully", "user_id": new_user.id}


@router.get("/", response_class=HTMLResponse)
async def root(request: Request, user=Depends(get_current_user)):
    lang_code = request.cookies.get("lang_code")
    if not lang_code:
        accept_language = request.headers.get("accept-language", "")
        lang_code = get_best_language_match(accept_language, SUPPORTED_LANGUAGES)
    templates.env.filters["t"] = get_translator_cached(lang_code)

    if request.session.get("user"):
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(request, "login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user=Depends(get_current_user),
    master_db: Session = Depends(get_master_db),
):
    # Re-hydrate is_superadmin if session pre-dates this flag
    if "is_superadmin" not in request.session:
        global_user_id = request.session.get("global_user_id")
        if global_user_id:
            gu = master_db.query(GlobalUser).filter_by(id=global_user_id).first()
            request.session["is_superadmin"] = bool(gu and gu.is_superadmin)
        else:
            request.session["is_superadmin"] = False

    return templates.TemplateResponse(
        request, "base.html",
        {
            "request": request,
            "title": "Dashboard",
            "user": user.username,
            "is_admin": user.admin,
            "is_superadmin": request.session.get("is_superadmin", False),
            "team": getattr(user.team, "name", ""),
        },
    )
