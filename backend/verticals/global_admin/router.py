import os
import subprocess

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, sessionmaker
from typing import Optional

from core.auth import get_current_superadmin
from core.database import get_master_db, _get_tenant_engine
from core.models.base import Base
from models.master import GlobalUser, LoginToken, Tenant, UserTenant
from templates import templates

router = APIRouter(
    prefix="/global-admin",
    tags=["global_admin"],
    dependencies=[Depends(get_current_superadmin)],
)


# --- Dashboard ---

@router.get("/", response_class=HTMLResponse, name="global_admin_dashboard")
async def global_admin_dashboard(request: Request, master_db: Session = Depends(get_master_db)):
    tenant_count = master_db.query(Tenant).count()
    user_count = master_db.query(GlobalUser).count()
    return templates.TemplateResponse(
        "global_admin/dashboard.html",
        {"request": request, "tenant_count": tenant_count, "user_count": user_count},
    )


# --- Tenants ---

@router.get("/tenants", response_class=HTMLResponse, name="global_admin_tenants")
async def tenants_list(request: Request, master_db: Session = Depends(get_master_db)):
    tenants = master_db.query(Tenant).order_by(Tenant.id).all()
    return templates.TemplateResponse(
        "global_admin/tenants.html",
        {"request": request, "tenants": tenants},
    )


@router.post("/tenants/create", response_class=HTMLResponse, name="global_admin_tenant_create")
async def tenant_create(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    require_2fa: Optional[str] = Form(None),
    master_db: Session = Depends(get_master_db),
):
    slug = slug.strip().lower()
    name = name.strip()

    if master_db.query(Tenant).filter_by(slug=slug).first():
        tenants = master_db.query(Tenant).order_by(Tenant.id).all()
        return templates.TemplateResponse(
            "global_admin/tenants.html",
            {"request": request, "tenants": tenants, "error": f"Slug '{slug}' already exists"},
        )

    # Derive DB path from the default DB location, namespaced by slug
    default_db = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    if default_db.startswith("sqlite:///"):
        db_path = default_db.rsplit("/", 1)[0] + f"/{slug}.db"
        db_url = f"sqlite:///{db_path.lstrip('sqlite:///')}"
    else:
        # Postgres: use same server, different DB name — admin must create the DB manually
        db_url = default_db.rsplit("/", 1)[0] + f"/{slug}"

    tenant = Tenant(slug=slug, name=name, db_url=db_url, require_2fa=require_2fa == "on")
    master_db.add(tenant)
    master_db.flush()

    # Provision schema in the new tenant DB
    # Must import all models to register them with Base.metadata before create_all
    import models.account, models.alarm, models.call, models.company  # noqa: F401
    import models.customer, models.invoice, models.product, models.product_customer  # noqa: F401
    import models.tag, models.team  # noqa: F401

    tenant_engine = _get_tenant_engine(db_url)
    Base.metadata.create_all(bind=tenant_engine)

    # Seed default CMS config
    from data.constants import seed_cms_config
    tenant_db_seed = sessionmaker(bind=tenant_engine)()
    try:
        seed_cms_config(tenant_db_seed)
    finally:
        tenant_db_seed.close()

    # Seed the requesting superadmin as a local user in the new tenant
    global_user_id = request.session.get("global_user_id")
    if global_user_id:
        master_db.add(UserTenant(global_user_id=global_user_id, tenant_id=tenant.id))

        from models.team import Team
        from core.models.models import User
        tenant_db = sessionmaker(bind=tenant_engine)()
        try:
            global_user = master_db.query(GlobalUser).filter_by(id=global_user_id).first()
            team = Team(name="Admin")
            tenant_db.add(team)
            tenant_db.flush()
            local_user = User(
                username=global_user.email,
                password_hash="",
                admin=1,
                global_user_id=global_user_id,
                team_id=team.id,
            )
            tenant_db.add(local_user)
            tenant_db.commit()
        finally:
            tenant_db.close()

    master_db.commit()

    tenants = master_db.query(Tenant).order_by(Tenant.id).all()
    return templates.TemplateResponse(
        "global_admin/tenants.html",
        {"request": request, "tenants": tenants, "saved_id": tenant.id},
    )


@router.get("/tenants/{tenant_id}/edit", response_class=HTMLResponse, name="global_admin_tenant_edit")
async def tenant_edit_form(
    request: Request,
    tenant_id: int,
    master_db: Session = Depends(get_master_db),
):
    tenant = master_db.query(Tenant).filter_by(id=tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return templates.TemplateResponse(
        "global_admin/tenant_edit.html",
        {"request": request, "tenant": tenant},
    )


@router.post("/tenants/{tenant_id}/edit", response_class=HTMLResponse)
async def tenant_edit_save(
    request: Request,
    tenant_id: int,
    name: str = Form(...),
    slug: str = Form(...),
    active: Optional[str] = Form(None),
    require_2fa: Optional[str] = Form(None),
    enabled_verticals: Optional[str] = Form(None),
    master_db: Session = Depends(get_master_db),
):
    tenant = master_db.query(Tenant).filter_by(id=tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant.name = name.strip()
    tenant.slug = slug.strip()
    tenant.active = active == "on"
    tenant.require_2fa = require_2fa == "on"
    tenant.enabled_verticals = enabled_verticals.strip() or None
    master_db.commit()

    tenants = master_db.query(Tenant).order_by(Tenant.id).all()
    return templates.TemplateResponse(
        "global_admin/tenants.html",
        {"request": request, "tenants": tenants, "saved_id": tenant_id},
    )


# --- Global Users ---

@router.get("/globalusers", response_class=HTMLResponse, name="global_admin_globalusers")
async def globalusers_list(request: Request, master_db: Session = Depends(get_master_db)):
    users = master_db.query(GlobalUser).order_by(GlobalUser.id).all()
    tenants = master_db.query(Tenant).order_by(Tenant.name).all()
    memberships = {
        u.id: [
            link.tenant_id
            for link in master_db.query(UserTenant).filter_by(global_user_id=u.id).all()
        ]
        for u in users
    }
    return templates.TemplateResponse(
        "global_admin/globalusers.html",
        {"request": request, "users": users, "tenants": tenants, "memberships": memberships},
    )


@router.post("/globalusers/create", response_class=HTMLResponse)
async def globaluser_create(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    master_db: Session = Depends(get_master_db),
):
    existing = master_db.query(GlobalUser).filter_by(email=email.strip()).first()
    if existing:
        users = master_db.query(GlobalUser).order_by(GlobalUser.id).all()
        tenants = master_db.query(Tenant).order_by(Tenant.name).all()
        memberships = {
            u.id: [l.tenant_id for l in master_db.query(UserTenant).filter_by(global_user_id=u.id).all()]
            for u in users
        }
        return templates.TemplateResponse(
            "global_admin/globalusers.html",
            {"request": request, "users": users, "tenants": tenants,
             "memberships": memberships, "error": f"Email {email} already exists"},
        )
    user = GlobalUser(email=email.strip())
    user.set_password(password)
    master_db.add(user)
    master_db.commit()
    return await globalusers_list(request, master_db)


@router.post("/globalusers/{user_id}/set-superadmin", response_class=HTMLResponse)
async def globaluser_set_superadmin(
    request: Request,
    user_id: int,
    is_superadmin: Optional[str] = Form(None),
    master_db: Session = Depends(get_master_db),
):
    user = master_db.query(GlobalUser).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_superadmin = is_superadmin == "on"
    master_db.commit()
    return await globalusers_list(request, master_db)


@router.post("/globalusers/{user_id}/assign-tenant", response_class=HTMLResponse)
async def globaluser_assign_tenant(
    request: Request,
    user_id: int,
    tenant_id: int = Form(...),
    master_db: Session = Depends(get_master_db),
):
    existing = master_db.query(UserTenant).filter_by(
        global_user_id=user_id, tenant_id=tenant_id
    ).first()
    if not existing:
        master_db.add(UserTenant(global_user_id=user_id, tenant_id=tenant_id))
        master_db.commit()
    return await globalusers_list(request, master_db)


@router.post("/globalusers/{user_id}/remove-tenant", response_class=HTMLResponse)
async def globaluser_remove_tenant(
    request: Request,
    user_id: int,
    tenant_id: int = Form(...),
    master_db: Session = Depends(get_master_db),
):
    link = master_db.query(UserTenant).filter_by(
        global_user_id=user_id, tenant_id=tenant_id
    ).first()
    if link:
        master_db.delete(link)
        master_db.commit()
    return await globalusers_list(request, master_db)


# --- Teams (per tenant) ---

def _get_tenant_session(db_url: str):
    from sqlalchemy.orm import sessionmaker
    from core.database import _get_tenant_engine
    engine = _get_tenant_engine(db_url)
    return sessionmaker(bind=engine)()


@router.get("/tenants/{tenant_id}/teams", response_class=HTMLResponse, name="global_admin_teams")
async def global_admin_teams(
    request: Request,
    tenant_id: int,
    master_db: Session = Depends(get_master_db),
):
    tenant = master_db.query(Tenant).filter_by(id=tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    from models.team import Team
    tenant_db = _get_tenant_session(tenant.db_url)
    try:
        teams = tenant_db.query(Team).order_by(Team.name).all()
        teams_data = [{"id": t.id, "name": t.name} for t in teams]
    finally:
        tenant_db.close()

    return templates.TemplateResponse(
        "global_admin/teams.html",
        {"request": request, "tenant": tenant, "teams": teams_data},
    )


@router.post("/tenants/{tenant_id}/teams/create", response_class=HTMLResponse)
async def global_admin_team_create(
    request: Request,
    tenant_id: int,
    name: str = Form(...),
    master_db: Session = Depends(get_master_db),
):
    tenant = master_db.query(Tenant).filter_by(id=tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    from models.team import Team
    tenant_db = _get_tenant_session(tenant.db_url)
    try:
        name = name.strip()
        existing = tenant_db.query(Team).filter_by(name=name).first()
        if existing:
            teams = tenant_db.query(Team).order_by(Team.name).all()
            teams_data = [{"id": t.id, "name": t.name} for t in teams]
            return templates.TemplateResponse(
                "global_admin/teams.html",
                {"request": request, "tenant": tenant, "teams": teams_data,
                 "error": f"Team '{name}' already exists."},
            )
        team = Team(name=name)
        tenant_db.add(team)
        tenant_db.commit()
        teams = tenant_db.query(Team).order_by(Team.name).all()
        teams_data = [{"id": t.id, "name": t.name} for t in teams]
    finally:
        tenant_db.close()

    return templates.TemplateResponse(
        "global_admin/teams.html",
        {"request": request, "tenant": tenant, "teams": teams_data, "saved": True},
    )


# --- Scripts ---

ALLOWED_SCRIPTS = {
    "migrate_all_tenants": "/app/backend/scripts/migrate_all_tenants.py",
}

SCRIPT_EXAMPLES = {
    "migrate_all_tenants": [
        "Migrera alla active tenants till senaste databasschema<br>(no arguments needed)"
    ],
}


def clean_output(raw_output: str) -> str:
    """Remove noisy output for nicer display."""
    lines = raw_output.splitlines()
    cleaned = []
    for line in lines:
        if any(keyword in line for keyword in [
            "PYTHONPATH",
            "/usr/local/lib/python",
            "site-packages",
            "UserWarning",
        ]):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


@router.get("/scripts", response_class=HTMLResponse, name="global_admin_scripts")
async def global_admin_scripts(request: Request):
    return templates.TemplateResponse(
        "global_admin/scripts.html",
        {"request": request, "output": None, "html_output": None, "scripts": ALLOWED_SCRIPTS, "script_examples": SCRIPT_EXAMPLES},
    )


@router.post("/scripts", response_class=HTMLResponse)
async def run_global_admin_script(
    request: Request,
    script_name: str = Form(...),
    args: str = Form(""),
):
    if script_name not in ALLOWED_SCRIPTS:
        return templates.TemplateResponse(
            "global_admin/scripts.html",
            {
                "request": request,
                "output": f"❌ Script '{script_name}' not found",
                "html_output": None,
                "scripts": ALLOWED_SCRIPTS,
                "script_examples": SCRIPT_EXAMPLES,
            },
        )

    script_path = ALLOWED_SCRIPTS[script_name]
    cmd = ["python", script_path] + args.split()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        output = result.stdout + result.stderr
        output = clean_output(output)

        return templates.TemplateResponse(
            "global_admin/scripts.html",
            {
                "request": request,
                "output": output,
                "html_output": None,
                "scripts": ALLOWED_SCRIPTS,
                "script_examples": SCRIPT_EXAMPLES,
            },
        )
    except subprocess.TimeoutExpired:
        output = "❌ Script timed out (5 minute limit)"
        return templates.TemplateResponse(
            "global_admin/scripts.html",
            {
                "request": request,
                "output": output,
                "html_output": None,
                "scripts": ALLOWED_SCRIPTS,
                "script_examples": SCRIPT_EXAMPLES,
            },
        )
    except Exception as e:
        output = f"❌ Error: {str(e)}"
        return templates.TemplateResponse(
            "global_admin/scripts.html",
            {
                "request": request,
                "output": output,
                "html_output": None,
                "scripts": ALLOWED_SCRIPTS,
                "script_examples": SCRIPT_EXAMPLES,
            },
        )
