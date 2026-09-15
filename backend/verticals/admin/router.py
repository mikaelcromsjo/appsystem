import csv
from io import StringIO
from fastapi import UploadFile, Form, File
from models.models import Customer, Call, Product, Team
from core.functions.helpers import formatPhoneNr
import json
from typing import List, Union

# admin.py
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi import APIRouter, Depends, Form, Request, HTTPException, Query
from models.models import User, Team
from models.master import GlobalUser, Tenant, UserTenant
from core.database import get_master_db

from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import Column, Integer, String, DateTime, JSON, select
from sqlalchemy.orm import Session, declarative_base
from typing import Optional
from datetime import datetime
from datetime import date
from sqlalchemy import select, and_
from datetime import date, timedelta
from core.auth import get_current_user
import subprocess, shlex
from typing import List, Optional
from core.models.base import Base
from pydantic import BaseModel
from pydantic import BaseModel, Field

from datetime import datetime

from core.database import get_db   
from templates import templates
from core.database import engine
from core.models.base import Base
from models.models import Update
from core.functions.helpers import populate

import subprocess

router = APIRouter(prefix="/admin", tags=["admin"])


# Whitelist of scripts admins can run
ALLOWED_SCRIPTS = {
    "manage_users": "/app/backend/scripts/manage_users.py",
    "stats": "/app/backend/scripts/generate_stats.py",
    "inspect_db": "/app/backend/scripts/inspect_db.py",    
}

SCRIPT_EXAMPLES = {
    "manage_users": [
        "Skapa en vanlig användare med lösenord och team Kalle<br>kalle --password hemlighet --team \"Kalle\"",
        "Skapa en administratörsanvändare med lösenord och team Admin<br>admin --password hemlighet --team \"Admin\" --admin 1",
        "Visa hjälp för kommandot<br>--help"
    ],
    "stats": [
        "Rita grafen 'calls_over_time' för daglig statistik (standardrange)<br>--chart calls_over_time",
        "Rita grafen 'team_performance' för månadens statistik<br>--chart team_performance",
        "Rita grafen 'product_participation' för vecka 2025-10-01 till 2025-10-07<br>--from 2025-10-01 --to 2025-10-07 --chart product_participation",
        "Visa daglig statistik för team Kalle<br>--team Kalle --chart calls_over_time",
        "Visa statistik för producttyp filter_a under oktober<br>--from 2025-10-01 --to 2025-10-31 --product-type filter_a --chart calls_over_time",
        "Generera rapport på engelska<br>--lang en --chart team_performance"
    ],
    "inspect_db": [
        "--database DATABASE [--limit LIMIT] [--filter FILTER]Visa databasdump<br>" 
    ]
}



@router.get("/script", response_class=HTMLResponse)
async def admin_script(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.admin <= 0:
        return HTMLResponse("Access denied", status_code=403)

    return templates.TemplateResponse(
        request, "admin/script.html",
        {"request": request, "output": None, "html_output": None, "scripts": ALLOWED_SCRIPTS, "script_examples": SCRIPT_EXAMPLES},
    )


def clean_output(raw_output: str) -> str:
    """Remove noisy PYTHONPATH and warnings for nicer display."""
    # Drop Python path and site-packages lines
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


@router.post("/script", response_class=HTMLResponse)
async def run_admin_script(
    request: Request,
    script_name: str = Form(...),
    args: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.admin <= 0:
        return HTMLResponse("Access denied", status_code=403)

    if script_name not in ALLOWED_SCRIPTS:
        return HTMLResponse("Invalid script", status_code=400)

    script_path = ALLOWED_SCRIPTS[script_name]

    try:
        arg_list = shlex.split(args) if args.strip() else ["--help"]
        command = ["python", script_path] + arg_list

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=20,
        )

        raw_output = (result.stdout or "") + (result.stderr or "")
        output = f"Running {script_name} {args}\n\n"
        output += clean_output(raw_output)
        output += f"\n\n[exit code: {result.returncode}]"

    except Exception as e:
        output = f"Running {script_name} {args}\n\n"
        output += f"⚠️ Error running script: {e}"


    html_output = None

    # --- Detect JSON message from script ---
    try:
        last_line = raw_output.strip().splitlines()[-1]
        info = json.loads(last_line)
        if info.get("html_created"):
            output_path = info.get("output_path", "/static/output.html")
            html_output = f'<iframe src="{output_path}" class="w-full h-[600px] border rounded-xl mt-4" style="height:100vh"></iframe>'
    except json.JSONDecodeError:
        print("Error")

    return templates.TemplateResponse(
        request, "admin/script_output.html",
        {"request": request, "output": output, "html_output": html_output, "scripts": ALLOWED_SCRIPTS, "script_examples": SCRIPT_EXAMPLES},
    )


# -----------------------------
# List Dashboard (HTMX fragment)
# -----------------------------
@router.get("/", response_class=HTMLResponse, name="admin_dashboard")
def admin_dashboard(
    request: Request,
    filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    

    return templates.TemplateResponse(
        request, "admin/dashboard.html", {"request": request }
    )


import json

def create_customer_from_row(row: dict, db):
    """
    Create a new Customer instance from a row dict.
    Safely handles missing, boolean, and JSON fields.
    """

    def _parse_json_field(value):
        """Parse JSON-like fields (list or dict), return default if invalid."""
        import json
        if not value:
            return []
        if isinstance(value, (list, dict)):
            return value
        try:
            return json.loads(value)
        except Exception:
            return []

    def _parse_bool(value):
        """Convert various truthy strings to bool."""
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in ["true", "1", "yes", "y", "t"]

    def _parse_tags(value):
        """Comma-separated tags"""
        if not value:
            return []
        return [v.strip().strip('"').strip("'") for v in value.split(",") if v.strip()]

    def _parse_id_list(value):
        """
        Parse CSV field into a list of string IDs.
        Accepts:
        - JSON array: '["1","2","3"]' or '[1,2,3]'
        - Comma-separated list: '1,2,3'
        - Single ID: '5'
        - Empty/None -> []
        Returns: list of strings, e.g. ["1", "2", "3"]
        """
        if not value:
            return []

        # Already a list or tuple
        if isinstance(value, (list, tuple)):
            return [str(v).strip() for v in value if str(v).strip()]

        s = str(value).strip()
        if not s:
            return []

        # Try JSON decode
        try:
            parsed = json.loads(s)
            if isinstance(parsed, (list, tuple)):
                return [str(v).strip() for v in parsed if str(v).strip()]
            elif parsed is not None:
                return [str(parsed).strip()]
            return []
        except Exception:
            # Fallback to comma-separated list
            parts = [p.strip() for p in s.split(",") if p.strip()]
            return [str(p) for p in parts]
            
# --- Team handling ---
    team = None
    team_name = row.get("team_name")
    if team_name:
        team_name = team_name.strip()
        if team_name:
            team = db.query(Team).filter(Team.name == team_name).first()
            if not team:
                team = Team(name=team_name)
                db.add(team)
                db.commit()
                db.refresh(team)

    new_customer = Customer(
        user_id=row.get("user_id") or "",
        first_name=row.get("first_name", "").strip(),
        last_name=row.get("last_name", "").strip(),
        code_name=_parse_bool(row.get("code_name")),
        email=row.get("email"),
        phone=formatPhoneNr(row.get("phone")),
        description_phone=row.get("description_phone"),
        location=row.get("location"),
        contributes=int(row.get("contributes") or 0) or None,
        comment=row.get("comment"),
        sub_caller=row.get("sub_caller"),
        organisations=_parse_id_list(row.get("organisations")),
        filters=_parse_id_list(row.get("filters")),
        categories=_parse_id_list(row.get("categories")),
        personality_type=int(row.get("personality_type") or 0) or None,
        controlled=_parse_bool(row.get("controlled")),
        is_filter_1=_parse_bool(row.get("is_filter_1")),
        is_filter_2=_parse_bool(row.get("is_filter_2")),
        is_filter_3=_parse_bool(row.get("is_filter_3")),
        is_filter_4=_parse_bool(row.get("is_filter_4")),
        is_filter_5=_parse_bool(row.get("is_filter_5")),
        is_filter_6=_parse_bool(row.get("is_filter_6")),
        is_filter_7=_parse_bool(row.get("is_filter_7")),
        is_filter_8=_parse_bool(row.get("is_filter_8")),
        tags=_parse_tags(row.get("tags")),
        extra=row.get("extra") if isinstance(row.get("extra"), dict) else {},
        # --- Team link ---
        team_id=team.id if team else None,
        team=team,
    )

    return new_customer

@router.get("/import", response_class=HTMLResponse, name="admin_import")
def admin_import(
    request: Request,
):

    return templates.TemplateResponse(
        request, "admin/import.html", {"request": request }
    )

@router.post("/import", response_class=HTMLResponse)
async def import_customers(
    request: Request,
    csv_text: str = Form(""),
    csv_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    content = ""

    # 1️⃣ Read content from either upload or text
    if csv_file:
        content = (await csv_file.read()).decode("utf-8")
    elif csv_text.strip():
        content = csv_text.strip()
    else:
        return templates.TemplateResponse(
            request, "partials/message.html",
            {"request": request, "message": "No CSV data provided."},
        )

    # 2️⃣ Parse CSV
    reader = csv.DictReader(StringIO(content))
    added, duplicates = [], []

    for row in reader:
        phone = formatPhoneNr(row.get("phone", ""))
        if not phone:
            continue

        existing = db.query(Customer).filter(Customer.phone == phone).first()
        if existing:
            duplicates.append(phone)
            continue

        # Create new customer record
        new_customer = create_customer_from_row(row, db)

        db.add(new_customer)
        added.append(phone)

    db.commit()

    # 3️⃣ Return summary (render partial)
    summary_html = f"""
    <div class='p-2 bg-gray-100 rounded'>
      <p><strong>Added:</strong> {len(added)} customers</p>
      <p><strong>Duplicates skipped:</strong> {len(duplicates)}</p>
      {("<p>Duplicate phones:</p><ul>" + "".join(f"<li>{p}</li>" for p in duplicates) + "</ul>") if duplicates else ""}
    </div>
    """
    return HTMLResponse(summary_html)

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
import json
from data.constants import CMS_CONFIG_KEY, load_cms_config
from models.config import TenantConfig


# --- User Management ---

def _get_users_context(db: Session, include_role_defs: bool = True) -> dict:
    """Helper to get context for users.html template."""
    from core.loader import get_nav_items
    users = db.query(User).order_by(User.id).all()
    teams = db.query(Team).order_by(Team.name).all()
    context = {"users": users, "teams": teams}
    if include_role_defs:
        nav_items = get_nav_items()
        context["verticals_with_roles"] = [v for v in nav_items if v.get("role_defs")]
    return context


@router.get("/users", response_class=HTMLResponse, name="admin_users")
def admin_users(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.admin <= 0:
        return HTMLResponse("Access denied", status_code=403)
    ctx = _get_users_context(db)
    return templates.TemplateResponse(
        request, "admin/users.html",
        {"request": request, **ctx},
    )


@router.post("/users/create", response_class=HTMLResponse)
async def admin_create_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    team_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    master_db: Session = Depends(get_master_db),
    user=Depends(get_current_user),
):
    if user.admin <= 0:
        return HTMLResponse("Access denied", status_code=403)

    email = email.strip()
    teams = db.query(Team).order_by(Team.name).all()

    existing_global = master_db.query(GlobalUser).filter_by(email=email).first()
    if existing_global:
        ctx = _get_users_context(db)
        return templates.TemplateResponse(
            request, "admin/users.html",
            {"request": request, **ctx, "error": f"Email '{email}' is already registered."},
        )

    # Resolve team: use given team_id or fall back to DEFAULT
    resolved_team_id = int(team_id) if team_id else None
    if not resolved_team_id:
        default_team = db.query(Team).filter_by(name="DEFAULT").first()
        if not default_team:
            default_team = Team(name="DEFAULT")
            db.add(default_team)
            db.flush()
        resolved_team_id = default_team.id

    global_user = GlobalUser(email=email)
    global_user.set_password(password)
    master_db.add(global_user)
    master_db.flush()

    tenant_slug = request.session.get("tenant_slug")
    tenant = master_db.query(Tenant).filter_by(slug=tenant_slug).first()
    if tenant:
        master_db.add(UserTenant(global_user_id=global_user.id, tenant_id=tenant.id))
    master_db.commit()

    new_user = User(username=email, team_id=resolved_team_id, global_user_id=global_user.id)
    db.add(new_user)
    db.commit()

    ctx = _get_users_context(db)
    return templates.TemplateResponse(
        request, "admin/users.html",
        {"request": request, **ctx, "saved": True},
    )


@router.post("/users/create-team", response_class=HTMLResponse, name="admin_create_team")
async def admin_create_team(
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.admin <= 0:
        return HTMLResponse("Access denied", status_code=403)

    name = name.strip()
    if not name:
        ctx = _get_users_context(db)
        return templates.TemplateResponse(
            request, "admin/users.html",
            {"request": request, **ctx, "error": "Team name cannot be empty."},
        )

    existing_team = db.query(Team).filter_by(name=name).first()
    if existing_team:
        ctx = _get_users_context(db)
        return templates.TemplateResponse(
            request, "admin/users.html",
            {"request": request, **ctx, "error": f"Team '{name}' already exists."},
        )

    team = Team(name=name)
    db.add(team)
    db.commit()

    ctx = _get_users_context(db)
    return templates.TemplateResponse(
        request, "admin/users.html",
        {"request": request, **ctx, "saved": True},
    )


@router.post("/users/{user_id}/update-team", response_class=HTMLResponse, name="admin_update_user_team")
async def admin_update_user_team(
    request: Request,
    user_id: int,
    team_id: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.admin <= 0:
        return HTMLResponse("Access denied", status_code=403)

    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        ctx = _get_users_context(db)
        return templates.TemplateResponse(
            request, "admin/users.html",
            {"request": request, **ctx, "error": "User not found."},
        )

    resolved_team_id = int(team_id) if team_id and team_id != "" else None
    target_user.team_id = resolved_team_id
    db.commit()

    ctx = _get_users_context(db)
    return templates.TemplateResponse(
        request, "admin/users.html",
        {"request": request, **ctx, "saved": True},
    )


@router.get("/users/{user_id}/detail", response_class=HTMLResponse, name="admin_user_detail")
def admin_user_detail(
    request: Request,
    user_id: int,
    list: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.admin <= 0:
        return HTMLResponse("Access denied", status_code=403)
    from core.loader import get_nav_items
    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        return HTMLResponse("User not found", status_code=404)
    teams = db.query(Team).order_by(Team.name).all()
    nav_items = get_nav_items()
    verticals_with_roles = [v for v in nav_items if v.get("role_defs")]
    template = "admin/user_info.html" if list == "short" else "admin/user_edit.html"
    return templates.TemplateResponse(request, template, {
        "request": request,
        "u": target_user,
        "teams": teams,
        "verticals_with_roles": verticals_with_roles,
    })


@router.post("/users/{user_id}/update", response_class=HTMLResponse, name="admin_update_user")
async def admin_update_user(
    user_id: int,
    team_id: Optional[str] = Form(None),
    admin: Optional[str] = Form(None),
    roles_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.admin <= 0:
        return HTMLResponse("Access denied", status_code=403)
    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        return HTMLResponse("User not found", status_code=404)

    target_user.team_id = int(team_id) if team_id else None
    target_user.admin = int(admin) if admin else 0

    if roles_json:
        try:
            import json as _json
            roles = _json.loads(roles_json)
            if isinstance(roles, dict):
                target_user.roles = {k: int(v) for k, v in roles.items()}
        except (ValueError, TypeError):
            pass

    db.commit()
    return HTMLResponse("", status_code=200)


@router.post("/users/{user_id}/set-admin", response_class=HTMLResponse, name="admin_update_user_admin")
async def admin_update_user_admin(
    request: Request,
    user_id: int,
    is_admin: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.admin <= 0:
        return HTMLResponse("Access denied", status_code=403)

    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        ctx = _get_users_context(db)
        return templates.TemplateResponse(
            request, "admin/users.html",
            {"request": request, **ctx, "error": "User not found."},
        )

    target_user.admin = 1 if is_admin == "on" else 0
    db.commit()

    ctx = _get_users_context(db)
    return templates.TemplateResponse(
        request, "admin/users.html",
        {"request": request, **ctx},
    )


@router.post("/users/{user_id}/remove-role", response_class=HTMLResponse, name="admin_remove_user_role")
async def admin_remove_user_role(
    request: Request,
    user_id: int,
    vertical: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.admin <= 0:
        return HTMLResponse("Access denied", status_code=403)

    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        ctx = _get_users_context(db)
        return templates.TemplateResponse(request, "admin/users.html", {"request": request, **ctx})

    roles = dict(target_user.roles or {})
    roles.pop(vertical, None)
    target_user.roles = roles
    db.commit()

    ctx = _get_users_context(db)
    return templates.TemplateResponse(request, "admin/users.html", {"request": request, **ctx})


@router.post("/users/{user_id}/add-role", response_class=HTMLResponse, name="admin_add_user_role")
async def admin_add_user_role(
    request: Request,
    user_id: int,
    vertical: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.admin <= 0:
        return HTMLResponse("Access denied", status_code=403)

    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        ctx = _get_users_context(db)
        return templates.TemplateResponse(request, "admin/users.html", {"request": request, **ctx})

    from core.loader import get_nav_items
    nav_items = get_nav_items()
    vertical_def = next((v for v in nav_items if v.get("slug") == vertical and v.get("role_defs")), None)

    roles = dict(target_user.roles or {})
    if vertical_def:
        full_mask = 0
        for bit in vertical_def["role_defs"].values():
            full_mask |= bit
        roles[vertical] = full_mask
    else:
        roles[vertical] = 1

    target_user.roles = roles
    db.commit()

    ctx = _get_users_context(db)
    return templates.TemplateResponse(request, "admin/users.html", {"request": request, **ctx})


@router.post("/users/{user_id}/update-roles", response_class=HTMLResponse, name="admin_update_user_roles")
async def admin_update_user_roles(
    request: Request,
    user_id: int,
    roles_json: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.admin <= 0:
        return HTMLResponse("Access denied", status_code=403)

    target_user = db.query(User).filter_by(id=user_id).first()
    if not target_user:
        ctx = _get_users_context(db)
        return templates.TemplateResponse(
            request, "admin/users.html",
            {"request": request, **ctx, "error": "User not found."},
        )

    try:
        import json
        roles = json.loads(roles_json)
        # Ensure it's a dict with string keys and int values
        if not isinstance(roles, dict):
            raise ValueError("Roles must be a JSON object")
        roles = {k: int(v) for k, v in roles.items()}
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        ctx = _get_users_context(db)
        return templates.TemplateResponse(
            request, "admin/users.html",
            {"request": request, **ctx, "error": f"Invalid roles JSON: {e}"},
        )

    target_user.roles = roles
    db.commit()

    ctx = _get_users_context(db)
    return templates.TemplateResponse(
        request, "admin/users.html",
        {"request": request, **ctx, "saved": True},
    )


def _cms_context(cfg: dict) -> dict:
    return {
        "categories_json":       json.dumps(cfg["categories"],               indent=2, ensure_ascii=False),
        "products_json":         json.dumps(cfg["products"],                 indent=2, ensure_ascii=False),
        "organisations_json":    json.dumps(cfg["organisations"],            indent=2, ensure_ascii=False),
        "filters_json":          json.dumps(cfg["filters"],                  indent=2, ensure_ascii=False),
        "personalities_json":    json.dumps(cfg["personalities"],            indent=2, ensure_ascii=False),
        "product_extras_json":   json.dumps(cfg.get("product_extras", {}),   indent=2, ensure_ascii=False),
        "customer_extras_json":  json.dumps(cfg.get("customer_extras", {}),  indent=2, ensure_ascii=False),
    }


@router.get("/data", response_class=HTMLResponse, name="admin_data")
def admin_data(request: Request, db: Session = Depends(get_db)):
    cfg = load_cms_config(db)
    return templates.TemplateResponse(
        request, "admin/data.html",
        {"request": request, **_cms_context(cfg)},
    )


@router.post("/data", response_class=HTMLResponse)
def save_data(
    request: Request,
    db: Session = Depends(get_db),
    categories_text: str = Form(...),
    products_text: str = Form(...),
    organisations_text: str = Form(...),
    filters_text: str = Form(...),
    personalities_text: str = Form(...),
    product_extras_text: str = Form(default="{}"),
    customer_extras_text: str = Form(default="{}"),
):
    try:
        cfg = {
            "categories":      json.loads(categories_text),
            "products":        json.loads(products_text),
            "organisations":   json.loads(organisations_text),
            "filters":         json.loads(filters_text),
            "personalities":   json.loads(personalities_text),
            "product_extras":  json.loads(product_extras_text),
            "customer_extras": json.loads(customer_extras_text),
        }
    except json.JSONDecodeError as e:
        return HTMLResponse(
            f"<div class='text-red-700 bg-red-100 border border-red-400 px-4 py-3 rounded-md'>Invalid JSON: {e}</div>",
            status_code=400,
        )

    row = db.query(TenantConfig).filter_by(key=CMS_CONFIG_KEY).first()
    if row:
        row.value = json.dumps(cfg, ensure_ascii=False)
    else:
        db.add(TenantConfig(key=CMS_CONFIG_KEY, value=json.dumps(cfg, ensure_ascii=False)))
    db.commit()

    return templates.TemplateResponse(
        request, "admin/data.html",
        {"request": request, **_cms_context(cfg), "message": "Saved."},
    )
