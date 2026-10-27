"""Read-only access to the extracted bot content (packages, forms, strings)."""
import json
from functools import lru_cache
from urllib.parse import urlparse
from . import config


@lru_cache
def _load(name: str):
    return json.loads((config.DATA_DIR / name).read_text(encoding="utf-8"))


def packages() -> dict:
    return {p["id"]: _with_safe_media(p) for p in _load("catalog_pdf.json")}


def _safe_media_url(value, *, local_prefix="/app/assets/"):
    if not isinstance(value, str) or not value:
        return None
    if local_prefix and value.startswith(local_prefix) and not value.startswith("//"):
        return value
    parsed = urlparse(value)
    if parsed.scheme == "https" and parsed.netloc:
        return value
    return None


def _localized_text(value):
    if not isinstance(value, dict):
        return {}
    return {lang: text for lang, text in value.items() if lang in {"en", "am"} and isinstance(text, str)}


def _with_safe_media(package: dict) -> dict:
    """Preserve package data while exposing only valid optional media metadata."""
    media = package.get("media")
    if not isinstance(media, dict):
        return package

    images = []
    for item in media.get("images", []):
        if not isinstance(item, dict):
            continue
        src = _safe_media_url(item.get("src"))
        if src:
            images.append({"src": src, "alt": _localized_text(item.get("alt"))})

    videos = []
    for item in media.get("videos", []):
        if not isinstance(item, dict):
            continue
        url = _safe_media_url(item.get("url") or item.get("src"))
        poster = _safe_media_url(item.get("poster"))
        if url:
            video = {"url": url, "title": _localized_text(item.get("title"))}
            if poster:
                video["poster"] = poster
            videos.append(video)

    result = dict(package)
    result["media"] = {"images": images, "videos": videos}
    return result


def forms() -> dict:
    return _load("forms.json")


def strings() -> dict:
    return _load("strings.json")


def ui() -> dict:
    return _load("ui_strings.json")


def deposit(price):
    return None if price is None else round(price * config.DEPOSIT_PERCENT / 100)


def money(n) -> str:
    return "-" if n is None else f"{n:,} ETB"


def public_config() -> dict:
    """Everything the frontend needs, in one payload."""
    return {
        "packages": list(packages().values()), "forms": forms(), "strings": strings(), "ui": ui(),
        "bank": {"name": config.BANK_NAME, "account_name": config.BANK_ACCOUNT_NAME,
                 "account_number": config.BANK_ACCOUNT_NUMBER, "deposit_percent": config.DEPOSIT_PERCENT},
        "contact": {"phones": config.CONTACT_PHONES, "website": config.WEBSITE},
    }
