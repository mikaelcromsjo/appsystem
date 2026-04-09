slug = "products"
label = "Products"
order = 20
admin_only = False

hx_endpoint = "products_list"
content_div_id = "product_content"


def get_routers():
    from routers import products
    return [products.router]
