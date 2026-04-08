# Compatibility re-export — import from domain-specific files instead.
__all__ = [
    "Update",
    "Alarm",
    "Call", "CallUpdate",
    "Caller",
    "Company", "CompanyUpdate",
    "Customer", "CustomerUpdate",
    "Invoice", "InvoiceNumber", "InvoiceUpdate",
    "Product", "ProductUpdate",
    "ProductCustomer",
]
from core.models.models import Update
from models.alarm import Alarm
from models.call import Call, CallUpdate
from models.caller import Caller
from models.company import Company, CompanyUpdate
from models.customer import Customer, CustomerUpdate
from models.invoice import Invoice, InvoiceNumber, InvoiceUpdate
from models.product import Product, ProductUpdate
from models.product_customer import ProductCustomer
