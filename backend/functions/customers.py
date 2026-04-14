

from sqlalchemy.orm import Session, declarative_base
from typing import List, Optional
from models.models import Customer, Team, Call
from sqlalchemy.orm import Session, joinedload
from core.models.base import Base
from fastapi import Request
from pydantic import BaseModel, Field
from core.functions.helpers import build_filters
from core.functions.filters import get_exact_vals, exact_vals
from typing import List, Optional
import datetime

class SelectedIDs(BaseModel):
    ids: List[int] = Field(..., alias="selected_ids")

def get_selected_ids(request: Request, selected_ids: Optional[SelectedIDs]) -> List[int]:
    """
    Helper to manage selected IDs in session.
    """

    if selected_ids is not None:
        # Save to session if POSTed
        request.session["selected_ids"] = selected_ids.ids
        return selected_ids.ids

    # Otherwise, pull from session
    return request.session.get("selected_ids", [])


def get_customers(db: Session, user, ids: List[int]) -> List[Customer]:
    """
    Helper to query customers from DB based on IDs.
    """
    query = db.query(Customer)
    if user.admin != 1:
        query = query.filter(Customer.team_id == user.team.id)
    if ids:
        query = query.filter(Customer.id.in_(ids))
    query = query.order_by(
        Customer.first_name.collate("NOCASE").asc(),
        Customer.last_name.collate("NOCASE").asc()
    )
    return query.all()

def assign_customers_team(db: Session, ids: List[int], team_id: int):
    """
    Assign multiple customers to a given team.
    Ensures team exists (even if in another DB) and updates customers safely.
    """

    if not ids:
        return 0  # nothing to do

    # Validate that team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise ValueError(f"Team with id {team_id} does not exist.")

    # Perform bulk update safely
    updated_rows = (
        db.query(Customer)
        .filter(Customer.id.in_(ids))
        .update({Customer.team_id: team_id}, synchronize_session="fetch")
    )

    db.commit()
    return updated_rows

def assign_customer_user(db: Session, ids: List[int], user_id: int):
    """
    Assign multiple customers to a given user.
    Ensures user exists and updates customers safely.
    """
    from models.models import User

    if not ids:
        return 0

    # Validate that user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} does not exist.")

    # Perform bulk update safely
    updated_rows = (
        db.query(Customer)
        .filter(Customer.id.in_(ids))
        .update({Customer.assigned_user_id: user_id}, synchronize_session="fetch")
    )

    db.commit()
    return updated_rows

def get_user_customers(db, request, user, json_fields: dict = None):
 #   calculate_last_call(db)
    query = db.query(Customer)

    if user.admin != 1:
        query = query.filter(Customer.assigned_user_id == user.id)

    filter_dict = request.session.get("customer_filters", {})
    filters = build_filters(filter_dict, Customer, json_fields=json_fields)

    sql_filters, exact_filters = get_exact_vals(filters)

    if sql_filters:
        query = query.filter(*sql_filters)

    query = query.order_by(
        Customer.first_name.collate("NOCASE").asc(),
        Customer.last_name.collate("NOCASE").asc()
    )
    rows = query.all()

    # Apply Python-side "exact" matching
    if exact_filters:
        rows = exact_vals(rows, exact_filters)

    return rows

def calculate_last_call(db: Session):
    customers = db.query(Customer).all()

    for customer in customers:
        last_call = (
            db.query(Call)
            .filter(Call.customer_id == customer.id)
            .filter(Call.status.in_([1, 3]))  # successful or answered calls
            .order_by(Call.call_date.desc())
            .first()
        )

        # Ensure `extra` exists and is a dict
        if customer.extra is None:
            customer.extra = {}

        if last_call:
            customer.last_call_date = last_call.call_date

    db.commit()