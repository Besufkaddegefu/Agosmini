"""Read-only access to the extracted bot content (packages, forms, strings)."""
import json
from functools import lru_cache
from . import config


@lru_cache
def _load(name: str):
    return json.loads((config.DATA_DIR / name).read_text(encoding="utf-8"))


def packages() -> dict:
    return {p["id"]: p for p in _load("catalog_pdf.json")}


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
