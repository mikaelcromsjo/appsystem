import json
from dataclasses import dataclass
from pathlib import Path

from fastapi import Depends

DATA_DIR = Path(__file__).parent

DEFAULT_TZ = "Europe/Stockholm"
SHOW_PRODUCTS_X_DAYS = 5

# --- Default CMS config (used as seed for new tenants) ---

def _load_defaults() -> dict:
    with open(DATA_DIR / "cms-config-default.json", "r", encoding="utf-8") as f:
        return json.load(f)

_defaults = _load_defaults()

categories    = _defaults["categories"]
products      = _defaults["products"]
organisations = _defaults["organisations"]
filters       = _defaults["filters"]
personalities = _defaults["personalities"]


# --- Derived lookup maps ---

def _build_maps(cfg: dict) -> dict:
    cats = cfg["categories"]
    prods = cfg["products"]
    orgs = cfg["organisations"]
    filts = cfg["filters"]
    pers = cfg["personalities"]

    categories_map: dict = {}
    for cid, cat in cats.items():
        categories_map[cid] = {"name": cat["name"], "type": "category"}
        for iid, item in cat["items"].items():
            categories_map[iid] = {"name": item, "parent": cid, "type": "item"}

    products_map: dict = {}
    for pid, prod in prods.items():
        products_map[pid] = {"name": prod["name"], "type": "product"}
        for iid, item in prod["items"].items():
            products_map[iid] = {"name": item, "parent": pid, "type": "options"}

    return {
        "categories_map":    categories_map,
        "products_map":      products_map,
        "organisations_map": {org["id"]: org["name"] for org in orgs},
        "filters_map":       {flt["id"]: flt["name"] for flt in filts},
        "personalities_map": {p["id"]: p for p in pers},
    }

_maps = _build_maps(_defaults)
categories_map    = _maps["categories_map"]
products_map      = _maps["products_map"]
organisations_map = _maps["organisations_map"]
filters_map       = _maps["filters_map"]
personalities_map = _maps["personalities_map"]


# --- DB helpers ---

CMS_CONFIG_KEY = "cms"


def load_cms_config(db) -> dict:
    """Load CMS config from tenant DB. Returns parsed dict."""
    from models.config import TenantConfig
    row = db.query(TenantConfig).filter_by(key=CMS_CONFIG_KEY).first()
    if row is None:
        raise RuntimeError("CMS config not found in tenant DB — was the tenant seeded?")
    return json.loads(row.value)


@dataclass
class CmsConfig:
    categories: dict
    products: dict
    organisations: list
    filters: list
    personalities: list
    categories_map: dict
    products_map: dict
    organisations_map: dict
    filters_map: dict
    personalities_map: dict


def get_cms_config(db=None) -> CmsConfig:
    """FastAPI dependency — inject as: cms: CmsConfig = Depends(get_cms_config)"""
    if db is None:
        from core.database import get_db
        raise RuntimeError("get_cms_config requires a db session via Depends(get_cms_config)")
    cfg = load_cms_config(db)
    maps = _build_maps(cfg)
    return CmsConfig(
        categories=cfg["categories"],
        products=cfg["products"],
        organisations=cfg["organisations"],
        filters=cfg["filters"],
        personalities=cfg["personalities"],
        **maps,
    )


# Wire up the FastAPI dependency injection
def _make_dependency():
    from core.database import get_db

    def _dep(db=Depends(get_db)) -> CmsConfig:
        cfg = load_cms_config(db)
        maps = _build_maps(cfg)
        return CmsConfig(
            categories=cfg["categories"],
            products=cfg["products"],
            organisations=cfg["organisations"],
            filters=cfg["filters"],
            personalities=cfg["personalities"],
            **maps,
        )
    return _dep

get_cms_config = _make_dependency()


def seed_cms_config(db) -> None:
    """Insert default CMS config into tenant DB if not already present."""
    from models.config import TenantConfig
    exists = db.query(TenantConfig).filter_by(key=CMS_CONFIG_KEY).first()
    if not exists:
        db.add(TenantConfig(key=CMS_CONFIG_KEY, value=json.dumps(_defaults, ensure_ascii=False)))
        db.commit()
