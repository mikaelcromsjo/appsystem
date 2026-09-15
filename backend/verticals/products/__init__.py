slug = "products"
label = "Products"
order = 20
admin_only = False

hx_endpoint = "products_list"
content_div_id = "product_content"

role_defs = {"ADMIN": 0b0001}


def get_routers():
    from verticals.products import router
    return [router.router]

COLUMNS = [
    {"key": "nr",         "label": "Nr",         "class": "w-[5%]"},
    {"key": "name",       "label": "Name",        "class": "w-[30%]"},
    {"key": "type",       "label": "Product Typ", "class": "w-[30%]"},
    {"key": "start_date", "label": "Start Date",  "class": "w-[30%]"},
    {"key": "command",    "label": "Command",     "class": "w-[30%]", "admin_only": True},
]
