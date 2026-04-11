slug = "companies"
label = "Companies"
order = 40
admin_only = False

hx_endpoint = "companies_list"
content_div_id = "companies_content"


def get_routers():
    from verticals.companies import router
    return [router.router]

COLUMNS = [
    {"key": "company_name", "label": "Company"},
    {"key": "name",         "label": "Name"},
    {"key": "email",        "label": "Email"},
    {"key": "group",        "label": "Group", "admin_only": True},
    {"key": "command",      "label": "Command"},
]
