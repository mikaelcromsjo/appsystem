slug = "accounts"
label = "Accounts"
order = 45
admin_only = False

hx_endpoint = "accounts_list"
content_div_id = "accounts_content"


def get_routers():
    from routers import accounts
    return [accounts.router]
