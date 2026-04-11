slug = "alarms"
label = "Alarms"
order = 40
admin_only = False

hx_endpoint = "alarms_list"
content_div_id = "alarm_content"


def get_routers():
    from verticals.alarms import router
    return [router.router]

COLUMNS = [
    {"key": "nr",       "label": "Nr"},
    {"key": "date",     "label": "Date"},
    {"key": "reminder", "label": "Reminder"},
    {"key": "customer", "label": "Customer"},
    {"key": "product",  "label": "Product"},
    {"key": "note",     "label": "Note"},
    {"key": "command",  "label": "Command"},
]
