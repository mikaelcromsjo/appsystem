from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from core.functions.helpers import render, populate
from templates import templates
from models.models import Company, CompanyUpdate, Team, Update
from core.auth import get_current_user
from data.constants import CmsConfig, get_cms_config


# -------------------------------------------------
# Router & Templates Setup
# -------------------------------------------------
router = APIRouter(prefix="/companies", tags=["companies"])

# -------------------------------------------------
# List Companies
# Returns an HTMX fragment with list.html
# -------------------------------------------------
@router.get("/", response_class=HTMLResponse, name="companies_list")
def companies_list(
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    query = db.query(Company)
    if(not user.admin):
        query = db.query(Company).filter(Company.team_id == user.team_id)
    companies = query.all()

    return render(
        "companies/list.html",
        {"request": request, 
         "companies": companies,
         },
    )


# -------------------------------------------------
# Company Detail
# Returns companies/edit.html
# -------------------------------------------------


@router.get("/new", response_class=HTMLResponse) 
def company_new(
    request: Request,
    db: Session = Depends(get_db),
    cms: CmsConfig = Depends(get_cms_config),
):

    company = Company.empty()

    query = db.query(Team)
    teams = query.all()

    return templates.TemplateResponse(
        "companies/edit.html",
        {
            "request": request, 
            "company": company, 
            "mode": "edit",
            "categories": cms.categories,
            "teams": teams, 
        }
    )



@router.post("/company/upsert", name="upsert_company", response_class=HTMLResponse)
async def upsert_company(
    request: Request,
    update_data: Update,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    # Determine if this is an update or create
    id = update_data.model_dump().get("id")
    if id:
        try:
            id_int = int(id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid Company ID")
        data_record = db.query(Company).filter(Company.id == id_int).first()
        if not data_record:
            raise HTTPException(status_code=404, detail="Company not found")
    else:
        data_record = Company()
        data_record.team_id = user.team_id

    data_dict = update_data.model_dump()

    # Ensure 'extra' exists and is a dict
    if 'extra' not in data_dict or not isinstance(data_dict['extra'], dict):
        data_dict['extra'] = {}

    # Move any keys that start with "extra." into the extra dict
    for key, value in list(data_dict.items()):
        if key.startswith("extra."):
            field_name = key.split(".", 1)[1]  # remove "extra."
            data_dict['extra'][field_name] = value
            del data_dict[key]  # optionally clean up the flat key
            
    # --- Temporarily remove relationships before populate ---
    team_id = (data_dict.pop("team_id", None))  # remove 'team' from dict
    if team_id:
        team_id = int(team_id)

    # Populate DB model dynamically (everything except relationships)
    data_record = populate(data_dict, data_record, CompanyUpdate)
    print ("team_id", team_id)
    # --- Handle relationships AFTER populate ---
    if isinstance(team_id, int):
        team_instance = db.get(Team, int(team_id))
        print ("instance", team_instance)
        if not team_instance:
            raise HTTPException(status_code=404, detail="Team not found")
        data_record.team = team_instance  # assign the actual SQLAlchemy object


    db.add(data_record)
    db.commit()
    db.refresh(data_record)

    # Render updated list (HTMX swap)
    query = db.query(Company)
    if(not user.admin):
        query = db.query(Company).filter(Company.team_id == user.team_id)
    companies = query.all()



    response =  templates.TemplateResponse(
        "companies/list.html",
        {
            "request": request, 
            "companies": companies,
            "detail": "Updated"},
    )
    # Set the popup message in a custom header
    response.headers["HX-Popup-Message"] = "Saved"
    return response




@router.get("/company/{company_id}", response_class=HTMLResponse)
def company_detail(
    request: Request,
    company_id: str,
    list: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    
    # Capture all query parameters as a dict
    query_params = dict(request.query_params)

    if (company_id and int(company_id) > 0):
        company = db.query(Company).filter(Company.id == int(company_id)).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company = (
            db.query(Company)
            .filter(Company.id == company_id)
            .first()
        )
    else:
        company = Company.empty()

    teams = (
        db.query(Caller)
        .all()
    )

    company.team_id = int(company.team_id) if company.team_id is not None else None

    print(company.to_dict())

# Example: log all query params
    print(f"Query params received: {query_params}")

    if list == "short":
        # Render short template
        return templates.TemplateResponse(
            "companies/info.html",
            {
                "request": request, 
                "company": company, 
                "company_id": company_id, 
                "teams": teams,
            }
        )
    else:
        # Render full template
        return templates.TemplateResponse(
            "companies/edit.html",
            {
                "request": request, 
                "company": company, 
            }
        )  
         

# DELETE company
@router.post("/delete/{company_id}", name="delete_company")
def delete_company(company_id: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db.delete(company)
    db.commit()
    return {"detail": f"Company {company_id} deleted successfully"}



