import hashlib, hmac, json, time
from datetime import datetime
from urllib.parse import urlencode
import pytest
from app import hours
from app.auth import validate_init_data, AuthError


def signed(token, **over):
    f = {"auth_date": str(int(time.time())), "user": json.dumps({"id": 42, "first_name": "Abebe"})}
    f.update(over)
    check = "\n".join(f"{k}={v}" for k, v in sorted(f.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    f["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(f)


def test_auth_ok_and_tamper():
    assert validate_init_data(signed("T"), "T")["id"] == 42
    with pytest.raises(AuthError):
        validate_init_data(signed("T"), "WRONG")
    with pytest.raises(AuthError):
        validate_init_data(signed("T", auth_date="1000"), "T")


@pytest.mark.parametrize("h,offline", [(7, False), (8, True), (13, True), (19, True), (20, False), (23, False), (0, False)])
def test_hours_gate(h, offline):
    assert hours.is_offline(datetime(2026, 10, 2, h, 30)) is offline


def test_ethiopian_clock_mapping():
    assert hours.ethiopian_clock(8) == (2, "morning")
    assert hours.ethiopian_clock(20) == (2, "evening")
    closed = hours.status(datetime(2026, 10, 2, 9, 0))
    assert closed["offline"] is True
    assert closed["reason_en"] and closed["reason_am"]
    assert hours.status(datetime(2026, 10, 2, 21, 0))["opens_at"] is None
