slug = "accounts"
label = "Accounts"
order = 45
admin_only = False

hx_endpoint = "accounts_list"
content_div_id = "accounts_content"


def get_routers():
    from verticals.accounts import router
    return [router.router]

COLUMNS = [
    {"key": "name",      "label": "Account"},
    {"key": "bank_name", "label": "Bank Name"},
    {"key": "iban",      "label": "IBAN"},
    {"key": "comment",   "label": "Comment",  "admin_only": True},
    {"key": "command",   "label": "Command"},
]
