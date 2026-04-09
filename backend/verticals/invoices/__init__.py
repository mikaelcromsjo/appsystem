slug = "invoices"
label = "Invoices"
order = 50
admin_only = False

hx_endpoint = "invoices_list"
content_div_id = "invoices_content"


def get_routers():
    from routers import invoices
    return [invoices.router]
