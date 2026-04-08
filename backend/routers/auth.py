import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from jose import jwt
from sqlalchemy.orm import Session

from core.auth import get_current_user
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, JWT_SECRET_KEY
from core.database import get_db
from core.i18n import clear_translator_cache, get_best_language_match, get_translator_cached
from core.config import SUPPORTED_LANGUAGES
from core.models.models import User
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
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    lang_code = request.cookies.get("lang_code")
    if not lang_code:
        accept_language = request.headers.get("accept-language", "")
        lang_code = get_best_language_match(accept_language, SUPPORTED_LANGUAGES)

    user = db.query(User).filter(User.username == username).first()
    if user and user.verify_password(password):
        request.session["authenticated"] = True
        request.session["admin"] = user.admin
        request.session["user"] = user.id
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "login.html", {"request": request, "error": "Invalid credentials"}
    )


@router.get("/logout")
@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    clear_translator_cache()
    return templates.TemplateResponse(
        "login.html", {"request": request, "message": "Logged out"}
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
    username: str = Form(...),
    password: str = Form(...),
    caller_id: int = Form(None),
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    if not current_user.admin:
        raise HTTPException(status_code=403, detail="Only admins can create users")

    new_user = User(username=username, caller_id=caller_id)
    new_user.set_password(password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"User {username} created successfully", "user_id": new_user.id}


@router.get("/", response_class=HTMLResponse)
async def root(request: Request, user=Depends(get_current_user)):
    lang_code = request.cookies.get("lang_code")
    if not lang_code:
        accept_language = request.headers.get("accept-language", "")
        lang_code = get_best_language_match(accept_language, SUPPORTED_LANGUAGES)
    templates.env.filters["t"] = get_translator_cached(lang_code)

    if request.session.get("user"):
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "title": "Dashboard",
            "user": user.username,
            "is_admin": user.admin,
            "caller": getattr(user.caller, "name", ""),
        },
    )
