slug = "companies"
label = "Companies"
order = 40
admin_only = False

hx_endpoint = "companies_list"
content_div_id = "companies_content"


def get_routers():
    from routers import companies
    return [companies.router]
