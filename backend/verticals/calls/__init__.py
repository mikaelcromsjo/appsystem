slug = "calls"
label = "Call Center"
order = 30
admin_only = False

hx_endpoint = "calls_dashboard"
content_div_id = "calls_content"


def get_routers():
    from routers import calls, teams
    return [calls.router, teams.router]
