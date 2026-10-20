"""Working-hours gate (same rule as the bot: offline while the team is on the phones)."""
from __future__ import annotations
from datetime import datetime, timedelta
import pytz
from . import config

TZ = pytz.timezone(config.TIMEZONE)


def _now(now: datetime | None) -> datetime:
    return TZ.localize(now) if now and now.tzinfo is None else (now or datetime.now(TZ)).astimezone(TZ)


def ethiopian_clock(hour24: int) -> tuple[int, str]:
    """Ethiopian clock: day starts at 6:00 standard time. 08:00 -> 2 (morning), 20:00 -> 2 (evening)."""
    h = (hour24 - 6) % 12 or 12
    return h, "morning" if 0 <= (hour24 - 6) % 24 < 12 else "evening"


def is_offline(now: datetime | None = None) -> bool:
    h = _now(now).hour
    return config.OFFLINE_START_HOUR <= h < config.OFFLINE_END_HOUR


def status(now: datetime | None = None) -> dict:
    n = _now(now)
    offline = is_offline(n)
    reopen = n.replace(hour=config.OFFLINE_END_HOUR, minute=0, second=0, microsecond=0)
    return {
        "offline": offline,                       # True -> show "please call" screen, block booking
        "opens_at": reopen.isoformat() if offline else None,
        "phone": config.CONTACT_PHONE,
        "offline_start_hour": config.OFFLINE_START_HOUR,
        "offline_end_hour": config.OFFLINE_END_HOUR,
        "reason_en": "Booking is unavailable while our team is assisting customers by phone during working hours.",
        "reason_am": "ቡድናችን በስራ ሰዓት ደንበኞችን በስልክ ስለሚያገለግል በዚህ ጊዜ ማዘዝ አይቻልም።",
        "ethiopian_window": "2:00 AM - 2:00 PM",
    }
