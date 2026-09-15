# alarms.py
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi import APIRouter, Depends, Form, Request, HTTPException, Query
from core.functions.helpers import local_to_utc, utc_to_local

from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import Column, Integer, String, DateTime, JSON, select
from sqlalchemy.orm import Session, declarative_base
from typing import Optional
from datetime import datetime
from datetime import date
from sqlalchemy import select, and_
from datetime import date, timedelta
from core.auth import get_current_user

from typing import List, Optional
from core.models.base import Base
from pydantic import BaseModel
from pydantic import BaseModel, Field

from datetime import datetime, timezone

from core.database import get_db   
from templates import templates
from core.database import engine
from core.models.base import Base
from models.models import Alarm
from models.models import Update
from core.functions.helpers import populate
from data.constants import CmsConfig, get_cms_config


router = APIRouter(prefix="/alarms", tags=["alarms"])

# -----------------------------
# List Alarms (HTMX fragment)
# -----------------------------
@router.get("/", response_class=HTMLResponse, name="alarms_list")
def alarms_list(
    request: Request,
    filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    # Check if there's an active filter in session
    filter_data = request.session.get("alarm_filters")

    query = db.query(Alarm).filter(Alarm.team_id == user.team_id)

    # Apply session-based filter if present
    if filter_data:
        if filter_data.get("show_all"):
            # User explicitly requested to show all alarms
            pass  # No additional filter
        elif filter_data.get("start") or filter_data.get("end"):
            start = filter_data.get("start")
            end = filter_data.get("end")
            if start and end:
                start_dt = datetime.fromisoformat(start)
                end_dt = datetime.fromisoformat(end)
                query = query.filter(Alarm.date >= start_dt, Alarm.date < end_dt)
            elif start:
                start_dt = datetime.fromisoformat(start)
                query = query.filter(Alarm.date >= start_dt)
            elif end:
                end_dt = datetime.fromisoformat(end)
                query = query.filter(Alarm.date < end_dt)
    else:
        # Default filter: show alarms from today onwards (only on first load)
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(Alarm.date >= today)

    alarms = query.all()

    from verticals.alarms import COLUMNS
    return templates.TemplateResponse(
        request, "alarms/list.html", {"request": request, "alarms": alarms, "columns": COLUMNS}
    )


@router.get("/rows", response_class=HTMLResponse, name="alarms_rows")
def alarms_rows(
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    # Check if there's an active filter in session
    filter_data = request.session.get("alarm_filters")

    query = db.query(Alarm).filter(Alarm.team_id == user.team_id)

    # Apply session-based filter if present
    if filter_data:
        if filter_data.get("show_all"):
            # User explicitly requested to show all alarms
            pass  # No additional filter
        elif filter_data.get("start") or filter_data.get("end"):
            start = filter_data.get("start")
            end = filter_data.get("end")
            if start and end:
                start_dt = datetime.fromisoformat(start)
                end_dt = datetime.fromisoformat(end)
                query = query.filter(Alarm.date >= start_dt, Alarm.date < end_dt)
            elif start:
                start_dt = datetime.fromisoformat(start)
                query = query.filter(Alarm.date >= start_dt)
            elif end:
                end_dt = datetime.fromisoformat(end)
                query = query.filter(Alarm.date < end_dt)
    else:
        # Default filter: show alarms from today onwards (only on first load)
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(Alarm.date >= today)

    alarms = query.all()
    return templates.TemplateResponse(
        request, "alarms/rows.html",
        {"request": request, "alarms": alarms},
    )



# -----------------------------
# Alarm Detail Modal (HTMX fragment)
# -----------------------------
@router.get("/new", name="new_alarm", response_class=HTMLResponse)
def new_alarm(
    request: Request,
    db: Session = Depends(get_db),
    cms: CmsConfig = Depends(get_cms_config),
):
    alarm = Alarm.empty()

    return templates.TemplateResponse(
        request, "alarms/edit.html", {"request": request, "alarm": alarm, "editable": True, "filters_json": cms.filters}
    )               

from urllib.parse import urlencode
from datetime import datetime

def get_google_calendar_link(alarm):
    event_title = f"Påminnelse: Ring Kund: {alarm.customer.first_name} {alarm.customer.last_name}"
#    start_time = alarm.date.strftime('%Y%m%dT%H%M%S')  # local time 
#    end_time = alarm.date.strftime('%Y%m%dT%H%M%S')    # same as start if no duration

    start_time = utc_to_local(alarm.date,'%Y%m%dT%H%M%S') 
    end_time = utc_to_local(alarm.date,'%Y%m%dT%H%M%S')


    details = alarm.note or ""
    reminder_minutes = int((alarm.date - alarm.reminder).total_seconds() // 60) if alarm.reminder else 10

    params = {
        "action": "TEMPLATE",
        "text": event_title,
        "dates": f"{start_time}/{end_time}",  # <-- include start and end
        "details": details,
        "trp": "true",
        "add": f"reminders:minutes:{reminder_minutes}"
    }

    return "https://www.google.com/calendar/render?" + urlencode(params)

# -----------------------------
# Alarm Detail Modal (HTMX fragment)
# -----------------------------
@router.get("/alarm/{alarm_id}", response_class=HTMLResponse)
def alarm_detail(
    request: Request,
    alarm_id: int,
    list: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    

    alarm = db.get(Alarm, alarm_id)
    if not alarm:
        alarm = Alarm().empty()
    
    google_calendar_link = get_google_calendar_link(alarm)

    if list == "short":
        # Render short template
        return templates.TemplateResponse(
            request, "alarms/info.html",
            {
                "request": request, 
                "alarm": alarm, 
                "google_calendar_link": google_calendar_link, 
            }
        )
    else:
        # Render full template
        return templates.TemplateResponse(
            request, "alarms/edit.html", {"request": request, "alarm": alarm, "editable": True}
        )
     




# DELETE alarm
@router.post("/delete/{alarm_id}", name="delete_alarm")
def delete_alarm(alarm_id: str, db: Session = Depends(get_db)):
    alarm = db.query(Alarm).filter(Alarm.id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")

    db.delete(alarm)
    db.commit()
    return {"detail": f"Alarm deleted successfully"}


# DELETE multiple alarms
class DeleteSelectedRequest(BaseModel):
    ids: list[int]


@router.post("/delete-selected", name="delete_alarms_selected", response_class=HTMLResponse)
def delete_alarms_selected(
    payload: DeleteSelectedRequest,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    db.query(Alarm).filter(
        Alarm.id.in_(payload.ids),
        Alarm.team_id == user.team_id,
    ).delete(synchronize_session=False)
    db.commit()
    return HTMLResponse("")


@router.post("/set_filter", name="set_filter", response_class=HTMLResponse)
async def set_filter(
    request: Request,
    db: Session = Depends(get_db),
):
    data = await request.json()

    from datetime import timedelta

    start_str = data.get("alarm_date_filter-start")
    end_str = data.get("alarm_date_filter-end")

    # If submitted with empty dates, set marker to show all
    if not start_str and not end_str:
        request.session["alarm_filters"] = {"show_all": True}
    else:
        alarm_date_filter_start = (
            datetime.fromisoformat(start_str) if start_str else None
        )
        alarm_date_filter_end = (
            datetime.fromisoformat(end_str) + timedelta(days=1) if end_str else None
        )

        # Store filter in session
        request.session["alarm_filters"] = {
            "start": alarm_date_filter_start.isoformat() if alarm_date_filter_start else None,
            "end": alarm_date_filter_end.isoformat() if alarm_date_filter_end else None,
        }

    response = HTMLResponse("")
    response.headers["HX-Trigger"] = "alarmsRowsReload"
    return response