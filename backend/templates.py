import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

core_templates_path = Path(__file__).parent / "core/templates"
app_templates_path = Path(__file__).parent / "templates"
verticals_path = Path(__file__).parent / "verticals"

vertical_template_dirs = [
    str(p / "templates")
    for p in sorted(verticals_path.iterdir())
    if p.is_dir() and not p.name.startswith("_") and (p / "templates").is_dir()
]

loader = ChoiceLoader([
    FileSystemLoader(vertical_template_dirs),
    FileSystemLoader(str(app_templates_path)),
    FileSystemLoader(str(core_templates_path)),
])

templates = Jinja2Templates(directory=str(app_templates_path))
templates.env.loader = loader

if os.environ.get("DEBUG", "false").lower() == "true":
    templates.env.cache = {}
    templates.env.auto_reload = True

templates.env.globals["now"] = lambda: datetime.now(timezone.utc)
templates.env.globals["timedelta"] = timedelta


def todatetime(value, fmts=None):
    if not value:
        return None
    fmts = fmts or [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue


templates.env.filters["todatetime"] = todatetime
