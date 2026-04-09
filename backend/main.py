"""
Entrypoint for the FastAPI + HTMX + Alpine.js prototype application.
"""

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from core.config import SESSION_SECRET
from core.database import engine, master_engine, init_admin_user
from core.models.base import Base
from models.master import MasterBase
from middleware import LanguageMiddleware
from scheduler import alarm_scheduler
from core.functions.helpers import utc_to_local
import core.loader as loader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HTMX + Alpine.js Prototype", debug=True)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401 and request.url.path not in ["/login", "/logout"]:
        return RedirectResponse(url="/login", status_code=303)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.add_middleware(LanguageMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="session",
    https_only=True,
)

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "core" / "static"), name="static")


@app.on_event("startup")
async def on_startup():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("✅ Database connected.")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return
    MasterBase.metadata.create_all(bind=master_engine)
    Base.metadata.create_all(bind=engine)
    init_admin_user()
    asyncio.create_task(alarm_scheduler())


from templates import templates
templates.env.filters["date"] = utc_to_local

# --- Infrastructure routers (always loaded, not verticals) ---
from routers import auth, user, tags

app.include_router(auth.router)
app.include_router(user.router, tags=["user"])
app.include_router(tags.router, tags=["tags"])

# --- Vertical routers (discovered from verticals/) ---
for _router in loader.get_routers():
    app.include_router(_router)

# --- Expose nav items to all templates ---
templates.env.globals["nav_verticals"] = loader.get_nav_items()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
