from threading import Lock
from core.lang import get_translator
from core.config import SUPPORTED_LANGUAGES

_translators_cache: dict = {}
_cache_lock = Lock()


def get_translator_cached(lang_code: str):
    with _cache_lock:
        if lang_code not in _translators_cache:
            _translators_cache[lang_code] = get_translator(lang_code)
        return _translators_cache[lang_code]


def clear_translator_cache():
    with _cache_lock:
        _translators_cache.clear()


def get_best_language_match(accept_language: str, supported: list[str]) -> str:
    if not accept_language:
        return supported[0]

    parsed = []
    for lang in accept_language.split(","):
        parts = lang.strip().split(";")
        code = parts[0].strip().split("-")[0]
        q = 1.0
        if len(parts) > 1 and parts[1].startswith("q="):
            try:
                q = float(parts[1][2:])
            except ValueError:
                pass
        parsed.append((code, q))

    parsed.sort(key=lambda x: x[1], reverse=True)
    for code, _ in parsed:
        if code in supported:
            return code
    return supported[0]
