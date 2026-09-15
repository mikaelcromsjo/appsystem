"""
Vertical discovery and loading.

Scans the `verticals/` directory for packages that declare a manifest
(slug, label, order, admin_only, hx_endpoint, content_div_id, get_routers).

Set ENABLED_VERTICALS=customers,calls,admin (comma-separated) to restrict
which verticals are loaded. Omit or leave empty to load all.
"""

import importlib
import os
from pathlib import Path
from types import ModuleType

_VERTICALS_DIR = Path(__file__).parent.parent / "verticals"

_loaded: list[ModuleType] = []


def discover() -> list[ModuleType]:
    """Import and return all enabled vertical modules, sorted by `order`."""
    if _loaded:
        return _loaded

    enabled_env = os.environ.get("ENABLED_VERTICALS", "").strip()
    enabled = set(enabled_env.split(",")) if enabled_env else None

    found = []
    for path in sorted(_VERTICALS_DIR.iterdir()):
        if not path.is_dir() or not (path / "__init__.py").exists():
            continue
        if path.name.startswith("_"):
            continue
        if enabled and path.name not in enabled:
            continue
        mod = importlib.import_module(f"verticals.{path.name}")
        found.append(mod)

    found.sort(key=lambda m: getattr(m, "order", 99))
    _loaded.extend(found)
    return _loaded


def get_routers():
    """Return all FastAPI routers from loaded verticals."""
    routers = []
    for v in discover():
        if callable(getattr(v, "get_routers", None)):
            routers.extend(v.get_routers())
    return routers


def get_nav_items() -> list[dict]:
    """
    Return nav descriptors for base.html.

    Each dict: slug, label, hx_endpoint, content_div_id, admin_only, role_defs.
    """
    return [
        {
            "slug": v.slug,
            "label": v.label,
            "hx_endpoint": v.hx_endpoint,
            "content_div_id": v.content_div_id,
            "admin_only": getattr(v, "admin_only", False),
            "superadmin_only": getattr(v, "superadmin_only", False),
            "role_defs": getattr(v, "role_defs", {}),
        }
        for v in discover()
    ]
