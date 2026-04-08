from templates import templates


def render(template_name: str, context: dict, base_template: str = "base.html"):
    """Return HTMX fragment or full page depending on request type."""
    request = context.get("request")
    if request is None:
        raise ValueError("context must include 'request'")
    template_name = template_name.lstrip("/")
    base_template = base_template.lstrip("/")
    if request.headers.get("hx-request"):
        return templates.TemplateResponse(template_name, context)
    ctx = context.copy()
    ctx["content_template"] = template_name
    return templates.TemplateResponse(base_template, ctx)
