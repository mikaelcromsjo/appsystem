# app/routers/teams.py

from fastapi import APIRouter, Depends, Request, Form, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from core.database import get_db
from templates import templates


from models.models import Customer, Call, Product, Team
from core.functions.helpers import render
from functions.customers import get_selected_ids, get_customers, get_user_customers, SelectedIDs


router = APIRouter(prefix="/calls", tags=["calls"])

# Create Team
@router.post("/admin/teams")
def create_team(name: str, db: Session = Depends(get_db)):
    team = Team(name=name)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team

# List Teams
@router.get("/admin/teams")
def list_teams(db: Session = Depends(get_db)):
    return db.query(Team).all()

# Delete Team
@router.delete("/admin/teams/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    db.delete(team)
    db.commit()
    return {"status": "deleted", "team_id": team_id}
