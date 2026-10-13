import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings


MESSAGE_DIRECTORY = Path(__file__).resolve().parent.parent / "messages"


@lru_cache(maxsize=4)
def _load_catalog(language):
    path = MESSAGE_DIRECTORY / f"{language}.json"
    with path.open(encoding="utf-8") as messages_file:
        return json.load(messages_file)


def _request_language(request=None):
    default = getattr(settings, "API_DEFAULT_LANGUAGE", "ar")
    if request is None:
        return default

    accepted = request.headers.get("Accept-Language", "")
    requested = accepted.split(",", 1)[0].split(";", 1)[0].strip().lower()
    if requested.startswith("en"):
        return "en"
    if requested.startswith("ar"):
        return "ar"
    return default


def resolve_message(code, request=None):
    language = _request_language(request)
    catalog = _load_catalog(language)
    return catalog.get(code) or _load_catalog("ar").get(code) or code
