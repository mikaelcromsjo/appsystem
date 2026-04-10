# Compatibility re-export — import from domain-specific files instead.
__all__ = [
    "Update",
    "Account", "AccountUpdate",
    "Alarm",
    "Call", "CallUpdate",
    "Team",
    "Company", "CompanyUpdate",
    "Customer", "CustomerUpdate",
    "Invoice", "InvoiceNumber", "InvoiceUpdate",
    "Product", "ProductUpdate",
    "ProductCustomer",
    "User", "UserUpdate",
    "Tag", "TagLink",
]

from models.base import Update
from models.account import Account, AccountUpdate
from models.alarm import Alarm
from models.call import Call, CallUpdate
from models.team import Team
from models.company import Company, CompanyUpdate
from models.customer import Customer, CustomerUpdate
from models.invoice import Invoice, InvoiceNumber, InvoiceUpdate
from models.product import Product, ProductUpdate
from models.product_customer import ProductCustomer
from models.user import User, UserUpdate
from models.tag import Tag, TagLink
