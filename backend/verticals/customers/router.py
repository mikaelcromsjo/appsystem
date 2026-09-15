from fastapi import APIRouter, Depends, Form, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
import json
from fastapi.responses import JSONResponse
from functions.customers import get_selected_ids, get_customers, SelectedIDs

from fastapi import FastAPI, Request, Form, status
from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import Session

from pydantic import BaseModel, Field

from typing import List, Optional, Dict, Any
from typing import Any, Union, Optional, get_origin, get_args

from core.models.base import Base
from core.database import get_db
from core.functions.helpers import render
from templates import templates

from data.constants import CmsConfig, get_cms_config

from models.models import Customer, CustomerUpdate, Team, ProductCustomer
from core.functions.helpers import populate, build_filters

from models.models import Update
from core.auth import get_current_user
from core.models.models import BaseMixin, Update, User

from functions.customers import get_user_customers
from functions.customers import get_selected_ids, assign_customers_team, SelectedIDs



# -------------------------------------------------
# Router & Templates Setup
# -------------------------------------------------
router = APIRouter(prefix="/customers", tags=["customers"])

# -------------------------------------------------
# List Customers
# Returns an HTMX fragment with list.html
# -------------------------------------------------


def to_comma_string(value):
    """Convert a list or JSON string of dicts to a comma-separated string."""
    if not value:
        return ''
    if isinstance(value, str):
        try:
            value = json.loads(value)  # Try to parse JSON string if needed
        except json.JSONDecodeError:
            return value  # Already a plain string
    if isinstance(value, list):
        return ', '.join(
            item.get('value', '') for item in value if isinstance(item, dict) and item.get('value')
        )
    return str(value)

@router.get("/", response_class=HTMLResponse, name="customers_list")
def customers_list(
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
    cms: CmsConfig = Depends(get_cms_config),
):
    from models.models import User
    customers = get_user_customers(db, request, user, json_fields=cms.customer_extras)
    teams = db.query(Team).all()
    users = db.query(User).all()

    from verticals.customers import COLUMNS
    return templates.TemplateResponse(
        request, "customers/list.html",
        {"request": request,
         "customers": customers,
         "is_admin": user.admin,
         "teams": teams,
         "users": users,
         "columns": COLUMNS,
        }
    )


@router.get("/rows", response_class=HTMLResponse, name="customers_rows")
def customers_rows(
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
    cms: CmsConfig = Depends(get_cms_config),
):
    from models.models import User
    customers = get_user_customers(db, request, user, json_fields=cms.customer_extras)
    users = db.query(User).all()
    return templates.TemplateResponse(
        request, "customers/rows.html",
        {"request": request, "customers": customers, "users": users},
    )

@router.post("/data", name="customers_data")
def customers_data(
    request: Request,
    selected_ids: Optional[SelectedIDs] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    ids = get_selected_ids(request, selected_ids)
    customers = get_customers(db, user, ids)

    # Convert SQLAlchemy objects → dict keyed by id
    customers_data = {
        c.id: {
            "id": c.id,
            "name": f"{c.first_name} {c.last_name}",
            "phone": c.phone
        }
        for c in customers
    }
    response = JSONResponse(content=customers_data)
    response.headers["HX-Popup-Message"] = "Loaded"
    return response


class AssignRequest(BaseModel):
    team_id: int
    selected_ids: SelectedIDs

class AssignUserRequest(BaseModel):
    user_id: int
    selected_ids: SelectedIDs

@router.post("/assign", response_class=HTMLResponse)
def assign_team(
    request: Request,
    data: AssignRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    team_id = data.team_id
    selected_ids = data.selected_ids

    # Extract list of IDs from form or session helper
    ids = get_selected_ids(request, selected_ids)
    team_id = int(team_id)

    if not ids:
        response = HTMLResponse("No customers selected", status_code=400)
        response.headers["HX-Popup-Message"] = "No customers selected"
        return response

    # Perform the safe DB update (validated in your CRUD helper)
    updated_count = assign_customers_team(db, ids, team_id)

    # Return an empty response with HTMX headers
    response = HTMLResponse("")  # empty body; HTMX will handle via headers
    response.headers["HX-Popup-Message"] = f"Assigned {updated_count} customers"
    response.headers["HX-Trigger"] = "customersReload"
    return response

@router.post("/assign_user", response_class=HTMLResponse)
def assign_user(
    request: Request,
    data: AssignUserRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    from functions.customers import assign_customer_user
    user_id = data.user_id
    selected_ids = data.selected_ids

    # Extract list of IDs from form or session helper
    ids = get_selected_ids(request, selected_ids)
    user_id = int(user_id)

    if not ids:
        response = HTMLResponse("No customers selected", status_code=400)
        response.headers["HX-Popup-Message"] = "No customers selected"
        return response

    # Perform the safe DB update
    updated_count = assign_customer_user(db, ids, user_id)

    # Return an empty response with HTMX headers
    response = HTMLResponse("")
    response.headers["HX-Popup-Message"] = f"Assigned {updated_count} customers"
    response.headers["HX-Trigger"] = "customersRowsReload"
    return response    


def validation_error(errors: list):
    return JSONResponse(
        status_code=422,
        content={"detail": errors}
    )

@router.post("/customer/upsert", name="upsert_customer", response_class=HTMLResponse)
async def upsert_customer(
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
            raise HTTPException(status_code=400, detail="Invalid Customer ID")
        data_record = db.query(Customer).filter(Customer.id == id_int).first()
        if not data_record:
            raise HTTPException(status_code=404, detail="Customer not found")
    else:
        data_record = Customer()

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

    assigned_user_id = (data_dict.pop("assigned_user_id", None))
    if assigned_user_id:
        assigned_user_id = int(assigned_user_id)

    # Populate DB model dynamically (everything except relationships)
    data_record = populate(data_dict, data_record, CustomerUpdate)
    # --- Handle relationships AFTER populate ---
    if isinstance(team_id, int):
        team_instance = db.get(Team, int(team_id))
        if not team_instance:
            raise HTTPException(status_code=404, detail="Team not found")
        data_record.team = team_instance  # assign the actual SQLAlchemy object

    if isinstance(assigned_user_id, int):
        from models.models import User
        user_instance = db.get(User, int(assigned_user_id))
        if not user_instance:
            raise HTTPException(status_code=404, detail="User not found")
        data_record.assigned_user = user_instance


    if data_record.location:
        data_record.location = to_comma_string(data_record.location)

    # Backend validation
    # Check for duplicates
    errors = []

    # Duplicate email
    if (data_record.email):
        duplicate_email = db.query(Customer).filter(Customer.id != id, Customer.email == data_record.email).first()
        if duplicate_email:
            errors.append({
                "loc": ["body", "email"],
                "msg": "Email already in system",
                "type": "value_error.conflict"
            })
    
    # Duplicate phone
    if (data_record.phone):
        duplicate_phone = db.query(Customer).filter(Customer.id != id, Customer.phone == data_record.phone).first()
        if duplicate_phone:
            errors.append({
                "loc": ["body", "phone"],
                "msg": "Phone numer already in system",
                "type": "value_error.conflict"
            })
    
    # Duplicate first + last name
    duplicate_name = db.query(Customer).filter(
        Customer.id != id,
        Customer.first_name == data_record.first_name,
        Customer.last_name == data_record.last_name
    ).first()
    if duplicate_name:
        errors.append({
            "loc": ["body", "first_name", "last_name"],
            "msg": "Customer name already in system",
            "type": "value_error.conflict"
        })

    # Return all validation errors if any
    if errors:
        return JSONResponse(status_code=422, content={"detail": errors})

    db.add(data_record)
    db.commit()
    db.refresh(data_record)

    response = HTMLResponse("")
    response.headers["HX-Popup-Message"] = "Saved"
    response.headers["HX-Trigger"] = json.dumps({"callsCustomersReload": True, "customersRowsReload": True})
    return response

@router.get("/customer/{customer_id}", response_class=HTMLResponse)
def customer_detail(
    request: Request,
    customer_id: str,
    user = Depends(get_current_user),
    list: str | None = Query(default=None),
    status_filter: int | None = Query(default=None),
    modal_store: str = Query(default="customers"),
    db: Session = Depends(get_db),
    cms: CmsConfig = Depends(get_cms_config),
):
    

    if (customer_id and int(customer_id) > 0):
        customer = db.query(Customer).filter(Customer.id == int(customer_id)).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )
    else:
        customer = Customer.empty()
        customer.team_id = user.team_id

    from models.models import User
    teams = db.query(Team).all()
    users = db.query(User).all()

    customer.team_id = int(customer.team_id) if customer.team_id is not None else None

    if list == "short":

    # Query product customers
        query = db.query(ProductCustomer).join(Customer).filter(ProductCustomer.customer_id == customer_id)
        product_customers = query.all()

        # Calculate totals per status
        totals = {"s1":0, "s2":0, "s3":0, "s4":0, "s5":0, "s6":0, "s7":0, "all":0}
        for ec in product_customers:
            totals["all"] += 1
            if ec.status == 2:
                totals["s2"] += 1
            elif ec.status == 1:
                totals["s1"] += 1
            elif ec.status == 3:
                totals["s3"] += 1
            elif ec.status == 4:
                totals["s4"] += 1
            elif ec.status == 5:
                totals["s5"] += 1
            elif ec.status == 6:
                totals["s6"] += 1
            elif ec.status == 7:
                totals["s7"] += 1

        
        if status_filter is not None:
            query = query.filter(ProductCustomer.status == status_filter)
        else:
            status_filter = 0
        product_customers = query.all()

        # Render short template
        return templates.TemplateResponse(
            request, "customers/info.html",
            {
                "request": request,
                "customer": customer,
                "customer_id": customer_id,
                "categories_map": cms.categories_map,
                "organisations_map": cms.organisations_map,
                "filters_map": cms.filters_map,
                "personalities_map": cms.personalities_map,
                "teams": teams,
                "product_customers": product_customers,
                "totals": totals,
                "status_filter": status_filter,
                "modal_store": modal_store,
                "customer_extras": cms.customer_extras,
            }
        )
    else:
        # Render full template
        return templates.TemplateResponse(
            request, "customers/edit.html",
            {
                "request": request,
                "customer": customer,
                "categories": cms.categories,
                "organisations": cms.organisations,
                "filters_json": cms.filters,
                "personalities": cms.personalities,
                "teams": teams,
                "users": users,
                "modal_store": modal_store,
                "customer_extras": cms.customer_extras,
            }
        )  
         

# DELETE customer
@router.post("/delete/{customer_id}", name="delete_customer")
def delete_customer(customer_id: str, db: Session = Depends(get_db), user = Depends(get_current_user)):
    from core.roles import user_has_role
    from verticals.customers.roles import ADMIN as CUSTOMERS_ADMIN

    if not user_has_role(user, "customers", CUSTOMERS_ADMIN):
        return {"detail": f"Access denied"}

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    db.delete(customer)
    db.commit()
    return {"detail": f"Customer {customer_id} deleted successfully"}



@router.get("/filter", response_class=HTMLResponse)
def customer_filter(
    request: Request,
    db: Session = Depends(get_db),
    cms: CmsConfig = Depends(get_cms_config),
):
        
    teams = (
        db.query(Team)
        .all()
    )

    filter_dict = request.session.get("customer_filters", {})

    return templates.TemplateResponse(
        request, "customers/filter.html",
        {
            "request": request,
            "filter_dict": filter_dict,
            "categories": cms.categories,
            "organisations": cms.organisations,
            "c_filters": cms.filters,
            "personalities": cms.personalities,
            "teams": teams,
            "customer_extras": cms.customer_extras,
        }
    )

from sqlalchemy import or_, and_

@router.post("/set_filter", name="set_filter", response_class=HTMLResponse)
async def set_filter(
    request: Request,
    update_data: Update,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    data_dict = update_data.model_dump()

    request.session["customer_filters"] = data_dict

    response = HTMLResponse("")
    response.headers["HX-Trigger"] = "customersRowsReload"
    return response
