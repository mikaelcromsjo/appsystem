slug = "invoices"
label = "Invoices"
order = 50
admin_only = False

hx_endpoint = "invoices_list"
content_div_id = "invoices_content"


def get_routers():
    from verticals.invoices import router
    return [router.router]

COLUMNS = [
    {"key": "id",      "label": "Invoice ID"},
    {"key": "number",  "label": "Invoice Number"},
    {"key": "date",    "label": "Date"},
    {"key": "note",    "label": "Note"},
    {"key": "company", "label": "Company"},
    {"key": "status",  "label": "Status"},
    {"key": "user",    "label": "User",     "admin_only": True},
    {"key": "command", "label": "Commands"},
]
