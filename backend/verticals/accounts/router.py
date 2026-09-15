from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from core.database import get_db
from core.functions.helpers import populate, build_filters
from core.auth import get_current_user
from templates import templates
from models.models import Account, Update, AccountUpdate

# -------------------------------------------------
# Router Setup
# -------------------------------------------------
router = APIRouter(prefix="/accounts", tags=["accounts"])

# -------------------------------------------------
# List
# -------------------------------------------------
@router.get("/", response_class=HTMLResponse, name="accounts_list")
def accounts_list(
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    from verticals.accounts import COLUMNS
    accounts = db.query(Account).all()
    return templates.TemplateResponse(
        request, "accounts/list.html",
        {"request": request, "accounts": accounts, "columns": COLUMNS}
    )


@router.get("/rows", response_class=HTMLResponse, name="accounts_rows")
def accounts_rows(
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    accounts = db.query(Account).all()
    return templates.TemplateResponse(
        request, "accounts/rows.html",
        {"request": request, "accounts": accounts},
    )

# -------------------------------------------------
# Detail / New
# -------------------------------------------------
@router.get("/{account_id}", response_class=HTMLResponse, name="account_detail")
def account_detail(
    request: Request,
    account_id: str,
    list: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    if int(account_id) > 0:
        account = db.query(Account).filter(Account.id == int(account_id)).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
    else:
        account = Account()

    if list == "short":
        return templates.TemplateResponse(
            request, "accounts/info.html",
            {"request": request, "account": account}
        )
    return templates.TemplateResponse(
        request, "accounts/edit.html",
        {"request": request, "account": account}  # Fixed: account only
    )

# -------------------------------------------------
# Create/Update
# -------------------------------------------------
@router.post("/upsert", name="upsert_account", response_class=HTMLResponse)
async def upsert_account(
    request: Request,
    update_data: Update,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    # Parse ID safely
    id = update_data.model_dump().get("id")
    if id:
        try:
            id_int = int(id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid Account ID")
        account = db.query(Account).filter(Account.id == id_int).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
    else:
        account = Account()

    data_dict = update_data.model_dump(exclude_unset=True)  # Only submitted fields

    # Extra dict handling (exact companies copy)
    if 'extra' not in data_dict or not isinstance(data_dict['extra'], dict):
        data_dict['extra'] = {}
    
    for key, value in list(data_dict.items()):
        if key.startswith("extra."):
            data_dict['extra'][key.split(".", 1)[1]] = value
            del data_dict[key]

    # Populate (match EXACT companies.py signature/order)
    account = populate(data_dict, account, AccountUpdate)  # Check this order!
    
    db.add(account)
    db.commit()
    db.refresh(account)

    response = HTMLResponse("")
    response.headers["HX-Popup-Message"] = "Saved"
    response.headers["HX-Trigger"] = "accountsRowsReload"
    return response

# -------------------------------------------------
# Delete
# -------------------------------------------------
@router.post("/delete/{account_id}", name="delete_account")
def delete_account(account_id: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    db.delete(account)
    db.commit()
    return {"detail": "Deleted"}
