slug = "alarms"
label = "Alarms"
order = 40
admin_only = False

hx_endpoint = "alarms_list"
content_div_id = "alarm_content"


def get_routers():
    from routers import alarms
    return [alarms.router]
