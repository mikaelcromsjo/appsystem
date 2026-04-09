slug = "global_admin"
label = "Global Admin"
order = 999
admin_only = False
superadmin_only = True

hx_endpoint = "global_admin_dashboard"
content_div_id = "global_admin_content"


def get_routers():
    from routers import global_admin
    return [global_admin.router]
