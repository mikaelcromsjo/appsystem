# Adding a New Entity

**Load: when creating new models or routers**

## Quick checklist

1. `models/<entity>.py` — `Base` from `core.models.base`, `BaseMixin` from `models.base`
2. Add re-export to `models/models.py`
3. `routers/<entity>.py` with `APIRouter`
4. Include router in `main.py`

## Detailed steps

### 1. Create the model

File: `backend/models/<entity>.py`

```python
from core.models.base import Base
from models.base import BaseMixin, Update
from sqlalchemy import Column, Integer, String, ForeignKey

class Entity(Base, BaseMixin):
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    team_id = Column(Integer, ForeignKey("teams.id"))

class EntityUpdate(Update):
    name: str | None = None
    team_id: int | None = None
```

**Rules:**
- Import `Base` from `core.models.base`
- Inherit `BaseMixin` from `models.base`
- Never import from `core.database`

### 2. Add re-export

File: `backend/models/models.py`

Add to the re-export imports:
```python
from models.entity import Entity, EntityUpdate
```

### 3. Create the router

File: `backend/routers/<entity>.py`

Use the CRUD Upsert pattern from `PATTERNS_CRUD.md`.

```python
from fastapi import APIRouter, Depends, Request
from core.database import get_db
from core.auth import get_current_user
from core.functions.render import render
from models import Entity, EntityUpdate

router = APIRouter(prefix="/<entities>")

@router.get("/", name="entities_list")
async def entities_list(request: Request, db=Depends(get_db), user=Depends(get_current_user)):
    entities = db.query(Entity).all()
    return render("entities/list.html", {"request": request, "entities": entities})
```

### 4. Register in main.py

Add to `backend/main.py`:
```python
from routers import entity
app.include_router(entity.router)
```

### 5. Create templates

Place fragments in `backend/templates/<entity>/`:
- `list.html` — full list page shell
- `rows.html` — reloadable rows fragment
- `edit.html` — create/edit form
- `info.html` — detail view

Use the Rows/Reload pattern from `PATTERNS_CRUD.md` for reactive lists.
