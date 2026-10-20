"""Booking validation and record building (the server is the source of truth for prices)."""
from __future__ import annotations
import hashlib, re, time
from datetime import datetime
from typing import Literal, Optional

import pytz
from pydantic import BaseModel, Field, ValidationError, field_validator

from . import catalog, config, ethcal

TZ = pytz.timezone(config.TIMEZONE)
_ET_MOBILE = re.compile(r"^(?:\+?251|0)?([79]\d{8})$")


class DateIn(BaseModel):
    day: int
    month: int
    year: int
    hour: int = Field(ge=1, le=12)
    period: Literal["morning", "afternoon", "evening", "night"]


class BookingIn(BaseModel):
    service: Literal["decor", "limo", "photo"]
    package: str
    name: str = Field(min_length=2, max_length=80)
    phone: str
    username: str = ""
    alt_phone: str = ""
    address: str = Field(min_length=3, max_length=400)
    gender: Optional[str] = None
    house: Optional[str] = None
    date: DateIn
    lang: Literal["en", "am"] = "en"

    @field_validator("name", "address", mode="before")
    @classmethod
    def _squash(cls, v):
        return " ".join(v.split()) if isinstance(v, str) else v


def normalize_phone(raw: str) -> str:
    s = re.sub(r"[\s\-().]", "", raw or "")
    m = _ET_MOBILE.match(s)
    if m:
        return "+251" + m.group(1)
    if re.fullmatch(r"\+?\d{8,15}", s):
        return s if s.startswith("+") else "+" + s
    raise ValueError("phone")


def normalize_username(raw: str) -> str:
    s = (raw or "").strip().replace("https://t.me/", "").lstrip("@")
    if not s:
        return ""
    if not re.fullmatch(r"[A-Za-z0-9_]{3,32}", s):
        raise ValueError("username")
    return "@" + s


class BookingError(Exception):
    def __init__(self, errors: dict, status: int = 422):
        super().__init__(errors)
        self.errors, self.status = errors, status


def today_addis():
    return datetime.now(TZ).date()


def parse_and_validate(payload_json: str) -> dict:
    """Return a clean booking dict or raise BookingError({field: code})."""
    try:
        b = BookingIn.model_validate_json(payload_json)
    except ValidationError as e:
        raise BookingError({str(err["loc"][0]) if err["loc"] else "payload": "invalid" for err in e.errors()})
    form = catalog.forms()[b.service]
    pkg = catalog.packages().get(b.package)
    errors: dict = {}

    if not pkg or pkg["service"] != b.service:
        errors["package"] = "invalid"
    phone = ""
    try:
        phone = normalize_phone(b.phone)
    except ValueError:
        errors["phone"] = "invalid"
    alt = ""
    if b.alt_phone.strip():
        try:
            alt = normalize_phone(b.alt_phone)
        except ValueError:
            errors["alt_phone"] = "invalid"
    username = ""
    try:
        username = normalize_username(b.username)
    except ValueError:
        errors["username"] = "invalid"
    for f in form["fields"]:
        if f["type"] == "choice" and getattr(b, f["id"], None) not in {o["v"] for o in f["options"]}:
            errors[f["id"]] = "invalid"

    d, gc = b.date, None
    if not ethcal.valid(d.year, d.month, d.day):
        errors["date"] = "invalid"
    else:
        gc = ethcal.to_gregorian(d.year, d.month, d.day)
        if gc < today_addis():
            errors["date"] = "past"
    if errors:
        raise BookingError(errors)

    per_en, per_am = ethcal.PERIODS[d.period]
    return {
        "service": b.service, "package_id": pkg["id"], "lang": b.lang,
        "name": b.name, "phone": phone, "alt_phone": alt, "username": username,
        "address": b.address, "gender": b.gender, "house": b.house,
        "date_text": f"{d.day:02d}/{d.month:02d}/{d.year}, {per_en} {d.hour}:00",
        "date_text_am": f"{d.day:02d}/{d.month:02d}/{d.year}, {per_am} {d.hour}፡00",
        "date_gc": gc.strftime("%d %b %Y"),
    }


def build_record(clean: dict, user: dict, now: datetime | None = None) -> dict:
    """Combine validated fields + package + user into the record used by PDF/notify."""
    now = now or datetime.now(TZ)
    form = catalog.forms()[clean["service"]]
    pkg = catalog.packages()[clean["package_id"]]
    price = pkg["price"]
    dep = catalog.deposit(price)
    tg_name = f"@{user['username']}" if user.get("username") else "-"
    gender = {"NotSure": "Not Sure"}.get(clean["gender"], clean["gender"]) or "-"
    values = {
        "name": clean["name"], "phone": clean["phone"], "alt_phone": clean["alt_phone"] or "-",
        "username": clean["username"] or tg_name,
        "address": clean["address"], "gender": gender, "house": clean["house"] or "-",
        "package": f"{pkg['title']['en']} ({catalog.money(price)})",
        "date": f"{clean['date_text']}  (Gregorian: {clean['date_gc']})",
    }
    return {
        "ref": f"{form['prefix']}-{now.strftime('%Y%m%d%H%M%S')}", "service": clean["service"],
        "form": form, "package": pkg, "price": price, "deposit": dep,
        "balance": None if price is None else price - dep, "values": values, "clean": clean, "created": now,
        "user": {"id": user["id"], "username": user.get("username"), "first_name": user.get("first_name", "")},
    }


# --- abuse protection (in-memory; fine for a single instance) -------------
_recent: dict = {}
_dedupe: dict = {}


def rate_limited(user_id: int, limit: int = 6, window: int = 3600) -> bool:
    now = time.time()
    hits = [t for t in _recent.get(user_id, []) if now - t < window]
    if len(hits) >= limit:
        _recent[user_id] = hits
        return True
    hits.append(now)
    _recent[user_id] = hits
    return False


def dedupe_key(user_id: int, payload_json: str, image: bytes) -> str:
    return f"{user_id}:{hashlib.sha256(payload_json.encode() + image).hexdigest()}"


def seen_recently(key: str, ttl: int = 600):
    now = time.time()
    for k in [k for k, (t, _) in _dedupe.items() if now - t > ttl]:
        _dedupe.pop(k, None)
    hit = _dedupe.get(key)
    return hit[1] if hit else None


def remember(key: str, ref: str) -> None:
    _dedupe[key] = (time.time(), ref)
