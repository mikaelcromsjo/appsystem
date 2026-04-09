slug = "customers"
label = "Customers"
order = 10
admin_only = False

# Tab behaviour
hx_endpoint = "customers_list"   # FastAPI route name for url_for()
content_div_id = "customer_content"


def get_routers():
    from routers import customers
    return [customers.router]
