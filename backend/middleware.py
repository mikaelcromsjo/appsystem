from core.i18n import get_translator_cached, get_best_language_match
from core.config import SUPPORTED_LANGUAGES
from templates import templates


class LanguageMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            from starlette.requests import Request
            request = Request(scope, receive=receive)

            lang_code = request.session.get("lang_code")
            if not lang_code:
                accept_language = request.headers.get("accept-language", "")
                lang_code = get_best_language_match(accept_language, SUPPORTED_LANGUAGES)
                request.session["lang_code"] = lang_code

            templates.env.filters["t"] = get_translator_cached(lang_code)

        await self.app(scope, receive, send)
