"""Validate Telegram Mini App initData (HMAC-SHA256) so requests can't be forged."""
from __future__ import annotations
import hashlib, hmac, json, time
from urllib.parse import parse_qsl


class AuthError(Exception):
    pass


def validate_init_data(init_data: str, bot_token: str, max_age: int = 86400) -> dict:
    """Return the Telegram user dict if init_data is authentic and fresh."""
    if not init_data:
        raise AuthError("missing initData")
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received = pairs.pop("hash", None)
    if not received:
        raise AuthError("missing hash")
    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise AuthError("bad signature")
    if time.time() - int(pairs.get("auth_date", "0")) > max_age:
        raise AuthError("initData expired")
    try:
        user = json.loads(pairs["user"])
    except (KeyError, ValueError):
        raise AuthError("missing user")
    return user
