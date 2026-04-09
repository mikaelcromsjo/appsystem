slug = "admin"
label = "Admin"
order = 100
admin_only = True

hx_endpoint = "admin_dashboard"
content_div_id = "admin_content"


def get_routers():
    from routers import admin
    return [admin.router]
