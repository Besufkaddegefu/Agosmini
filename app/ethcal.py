"""Ethiopian calendar helpers (customers give dates like 21/08/2018 in the bot)."""
from datetime import date

MONTHS = [
    ("Meskerem", "መስከረም"), ("Tikimt", "ጥቅምት"), ("Hidar", "ኅዳር"), ("Tahsas", "ታኅሣሥ"),
    ("Tir", "ጥር"), ("Yekatit", "የካቲት"), ("Megabit", "መጋቢት"), ("Miazia", "ሚያዝያ"),
    ("Ginbot", "ግንቦት"), ("Sene", "ሰኔ"), ("Hamle", "ሐምሌ"), ("Nehase", "ነሐሴ"), ("Pagume", "ጳጉሜን"),
]
PERIODS = {
    "morning": ("Morning", "ጥዋት"), "afternoon": ("Afternoon", "ከሰዓት"),
    "evening": ("Evening", "ማታ"), "night": ("Night", "ሌሊት"),
}
_OFFSET = 1723856


def is_leap(y: int) -> bool:
    return y % 4 == 3


def days_in_month(y: int, m: int) -> int:
    return 30 if m <= 12 else (6 if is_leap(y) else 5)


def valid(y: int, m: int, d: int) -> bool:
    return y > 0 and 1 <= m <= 13 and 1 <= d <= days_in_month(y, m)


def to_gregorian(y: int, m: int, d: int) -> date:
    jdn = _OFFSET + 365 * y + y // 4 + 30 * m + d - 31
    return date.fromordinal(jdn - 1721425)


def from_gregorian(dt: date):
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    r = (jdn - _OFFSET) % 1461
    n = r % 365 + 365 * (r // 1460)
    year = 4 * ((jdn - _OFFSET) // 1461) + r // 365 - r // 1460
    return year, n // 30 + 1, n % 30 + 1
