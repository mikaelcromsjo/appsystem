slug = "customers"
label = "Customers"
order = 10
admin_only = False

# Tab behaviour
hx_endpoint = "customers_list"   # FastAPI route name for url_for()
content_div_id = "customer_content"


def get_routers():
    from verticals.customers import router
    return [router.router]

COLUMNS = [
    {"key": "nr",       "label": "Nr",       "class": "w-[5%]"},
    {"key": "name",     "label": "Name",     "class": "w-[30%]", "sortable": True},
    {"key": "email",    "label": "Email",    "class": "w-[20%]"},
    {"key": "phone",    "label": "Phone",    "class": "w-[20%]"},
    {"key": "location", "label": "Location", "class": "w-[20%]"},
    {"key": "team",     "label": "Caller",   "class": "w-[20%]", "admin_only": True},
    {"key": "command",  "label": "Command",  "class": "w-[20%]"},
]
