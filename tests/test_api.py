import asyncio, json
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import bookings, catalog, ethcal, hours, notify
from app.main import app

H = {"x-dev-user": json.dumps({"id": 42, "first_name": "Abebe", "username": "abebe"})}


@pytest.fixture(autouse=True)
def online(monkeypatch):
    monkeypatch.setattr(hours, "status", lambda now=None: {"offline": False, "opens_at": None, "phone": "x", "ethiopian_window": "x"})
    bookings._recent.clear(); bookings._dedupe.clear(); notify.REGISTRY.clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def png(size=(800, 1600)):
    b = BytesIO(); Image.new("RGB", size, "white").save(b, "PNG"); return b.getvalue()


def payload(service="decor", pkg="decor_basic", **kw):
    p = {"service": service, "package": pkg, "name": "Abebe Kebede", "phone": "0911223344", "username": "@abebe",
         "address": "Bole, Addis Ababa", "date": {"day": 5, "month": 1, "year": 2040, "hour": 4, "period": "morning"}}
    if service == "decor":
        p.update(gender="Male", house="Villa")
    p.update(kw); return p


def post(client, p, img=None, headers=H):
    return client.post("/api/bookings", data={"payload": json.dumps(p)},
                       files={"screenshot": ("pay.png", img or png(), "image/png")}, headers=headers)


def test_requires_telegram_auth(client):
    assert client.get("/api/config").status_code == 401
    assert post(client, payload(), headers={}).status_code == 401


def test_config_has_everything(client):
    j = client.get("/api/config", headers=H).json()
    assert len(j["packages"]) == 12 and set(j["forms"]) == {"decor", "limo", "photo"}
    prices = {p["id"]: p["price"] for p in j["packages"]}
    assert prices["decor_special"] == 48000
    assert prices["limo_grand"] == 35000
    assert prices["limo_special"] == 45000
    assert prices["limo_royal"] == 50000
    assert prices["photo_standard"] == 16000
    assert j["user"]["id"] == 42 and "payment_notice" in j["strings"] and j["bank"]["deposit_percent"] == 50
    assert all(p["media"] == {"images": [], "videos": []} for p in j["packages"])


def test_media_normalization_keeps_only_safe_urls():
    package = {"id": "demo", "media": {
        "images": [{"src": "/app/assets/media/demo/01.webp", "alt": {"en": "Example", "am": "ምሳሌ"}},
                   {"src": "javascript:alert(1)"}],
        "videos": [{"url": "https://cdn.example/video.mp4", "poster": "/app/assets/media/demo/poster.webp"},
                   {"url": "http://insecure.example/video.mp4"},
                   {"url": "https://www.youtube.com/watch?v=abc"}]}}
    safe = catalog._with_safe_media(package)
    assert [i["src"] for i in safe["media"]["images"]] == ["/app/assets/media/demo/01.webp"]
    assert [v["url"] for v in safe["media"]["videos"]] == ["https://cdn.example/video.mp4", "https://www.youtube.com/watch?v=abc"]


def test_static_app_served(client):
    r = client.get("/app/")
    assert r.status_code == 200 and "AGOS" in r.text
    assert client.get("/app/js/app.js").status_code == 200 and client.get("/health").json() == {"ok": True}


@pytest.mark.parametrize("svc,pkg,prefix", [("decor", "decor_deluxe", "DEC"), ("limo", "limo_royal", "LIMO"),
                                            ("photo", "videography", "PHOTO"), ("photo", "photo_digital", "PHOTO")])
def test_booking_each_service(client, svc, pkg, prefix):
    r = post(client, payload(svc, pkg))
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ref"].startswith(prefix) and j["deposit"] == round(j["price"] / 2) and j["pdf_sent"] is True


def test_duplicate_submit_is_not_resent(client):
    img = png()
    a = post(client, payload(), img).json(); b = post(client, payload(), img).json()
    assert b["duplicate"] and a["ref"] == b["ref"]


def test_validation_errors(client):
    assert "phone" in post(client, payload(phone="123")).json()["errors"]
    assert "package" in post(client, payload(pkg="limo_grand")).json()["errors"]
    assert "date" in post(client, payload(date={"day": 30, "month": 13, "year": 2040, "hour": 4, "period": "morning"})).json()["errors"]
    assert post(client, payload(date={"day": 1, "month": 1, "year": 2010, "hour": 4, "period": "morning"})).json()["errors"]["date"] == "past"
    assert "gender" in post(client, payload(gender="Robot")).json()["errors"]
    assert "username" in post(client, payload(username="a b!")).json()["errors"]
    assert "name" in post(client, payload(name="A")).json()["errors"]


def test_bad_image_and_missing(client):
    r = post(client, payload(), img=b"not an image")
    assert r.status_code == 422 and "screenshot" in r.json()["errors"]


def test_offline_blocks_server_side(client, monkeypatch):
    monkeypatch.setattr(hours, "status", lambda now=None: {"offline": True, "opens_at": "x", "phone": "x", "ethiopian_window": "x"})
    r = post(client, payload())
    assert r.status_code == 403 and r.json()["error"] == "offline"


def test_rate_limit(client):
    codes = [post(client, payload(), png((100 + i, 100))).status_code for i in range(8)]
    assert codes[:6] == [200] * 6 and codes[6] == 429


def test_phone_and_username_normalisation():
    for raw in ["0911223344", "+251911223344", "911223344", "251 911 22 33 44", "07 11 22 33 44"]:
        assert bookings.normalize_phone(raw).startswith("+251") and len(bookings.normalize_phone(raw)) == 13
    assert bookings.normalize_username("https://t.me/abebe_k") == "@abebe_k"
    assert bookings.normalize_username("") == ""


def test_ethiopian_calendar():
    from datetime import date
    assert ethcal.to_gregorian(2019, 1, 1) == date(2026, 9, 11)
    assert ethcal.from_gregorian(date(2026, 9, 11)) == (2019, 1, 1)
    assert ethcal.valid(2015, 13, 6) and not ethcal.valid(2016, 13, 6) and not ethcal.valid(2016, 2, 31)
    import random
    for _ in range(3000):
        d = date.fromordinal(random.randint(date(2000, 1, 1).toordinal(), date(2040, 1, 1).toordinal()))
        assert ethcal.to_gregorian(*ethcal.from_gregorian(d)) == d


# ---- notify with a fake bot -------------------------------------------------
class FakeBot:
    def __init__(self, fail_for=()):
        self.calls, self.fail_for = [], set(fail_for)

    async def send_photo(self, chat_id, **kw):
        if chat_id in self.fail_for:
            from telegram.error import TelegramError
            raise TelegramError("blocked")
        self.calls.append(("photo", chat_id, kw)); return type("M", (), {"message_id": len(self.calls)})()

    async def send_message(self, chat_id, text, **kw):
        self.calls.append(("msg", chat_id, text)); return type("M", (), {"message_id": len(self.calls)})()

    async def send_document(self, chat_id, **kw):
        self.calls.append(("doc", chat_id, kw))

    async def edit_message_caption(self, *a, **kw): self.calls.append(("editcap", a, kw))
    async def edit_message_reply_markup(self, *a, **kw): self.calls.append(("editkb", a, kw))
    async def edit_message_text(self, *a, **kw): self.calls.append(("edittext", a, kw))


def make_record(**kw):
    return bookings.build_record(bookings.parse_and_validate(json.dumps(payload(**kw))), {"id": 42, "username": "abebe"})


def test_send_booking_reaches_admins_and_client():
    rec, bot = make_record(), FakeBot()
    res = asyncio.run(notify.send_booking(bot, rec, b"img", b"pdf"))
    kinds = [(c[0], c[1]) for c in bot.calls]
    assert res == {"admins_ok": 2, "admins_total": 2, "client_ok": True}
    assert ("photo", 111) in kinds and ("doc", 111) in kinds and ("photo", 222) in kinds and ("doc", 42) in kinds
    photo = next(c for c in bot.calls if c[0] == "photo")
    assert len(photo[2]["caption"]) <= 1024 and rec["ref"] in photo[2]["caption"]


def test_one_admin_failing_does_not_block_others():
    assert asyncio.run(notify.send_booking(FakeBot(fail_for={111}), make_record(), b"i", b"p"))["admins_ok"] == 1


def test_long_text_falls_back_to_separate_message():
    rec, bot = make_record(), FakeBot()
    rec["values"]["address"] = "ቦሌ " * 200
    asyncio.run(notify.send_booking(bot, rec, b"i", b"p"))
    assert any(c[0] == "msg" and c[1] == 111 for c in bot.calls)


def test_html_is_escaped_in_admin_text():
    rec = make_record(name="<b>Hacker</b> & Co")
    assert "<b>Hacker</b>" not in notify.admin_text(rec) and "&lt;b&gt;Hacker&lt;/b&gt;" in notify.admin_text(rec)


def test_confirm_notifies_client_once():
    rec, bot = make_record(), FakeBot()
    asyncio.run(notify.send_booking(bot, rec, b"i", b"p")); bot.calls.clear()
    assert "Confirmed" in asyncio.run(notify.decide(bot, "cfm", rec["ref"], 42, "Sara", None))
    assert any(c[0] == "msg" and c[1] == 42 and "confirmed" in c[2] for c in bot.calls)
    assert asyncio.run(notify.decide(bot, "rej", rec["ref"], 42, "Sara", None)).startswith("Already")
