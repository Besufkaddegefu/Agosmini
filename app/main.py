"""FastAPI server: serves the Mini App, validates Telegram users, takes bookings, hosts the bot webhook."""
from __future__ import annotations
import json, logging
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from tempfile import gettempdir

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from telegram import InputFile, Update

from . import bookings, bot as botmod, catalog, config, hours, notify, pdf
from .auth import AuthError, validate_init_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("agos")
MAX_UPLOAD = 10 * 1024 * 1024
DEV_OUT = Path(gettempdir()) / "agos_dev_out"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ptb = None
    if not config.ADMIN_IDS:
        log.error("No ADMIN_ID_1..3 configured: bookings will have nobody to notify")
    if config.DEV_MODE:
        log.warning("DEV_MODE is ON: unsigned users accepted and Telegram is NOT contacted. Never use in production.")
    elif config.BOT_TOKEN:
        app.state.ptb = botmod.build_application()
        await app.state.ptb.initialize()
        await app.state.ptb.start()
        try:
            await botmod.configure(app.state.ptb)
        except Exception:
            log.exception("webhook/menu configuration failed")
    else:
        log.error("BOT_TOKEN is not set")
    yield
    if app.state.ptb:
        await app.state.ptb.stop()
        await app.state.ptb.shutdown()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


def current_user(x_telegram_init_data: str = Header(default=""), x_dev_user: str = Header(default="")) -> dict:
    if config.DEV_MODE and x_dev_user:
        return json.loads(x_dev_user)
    try:
        return validate_init_data(x_telegram_init_data, config.BOT_TOKEN)
    except AuthError as e:
        raise HTTPException(401, f"unauthorized: {e}")


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/api/config")
async def api_config(user: dict = Depends(current_user)):
    return {**catalog.public_config(), "hours": hours.status(),
            "user": {"id": user["id"], "first_name": user.get("first_name", ""), "username": user.get("username", "")}}


def _prepare_image(raw: bytes) -> bytes:
    """Validate the screenshot and normalise it to a reasonably sized JPEG (also strips metadata)."""
    try:
        im = Image.open(BytesIO(raw))
        im.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise bookings.BookingError({"screenshot": "invalid"})
    im = im.convert("RGB")
    im.thumbnail((2000, 2000))
    out = BytesIO()
    im.save(out, "JPEG", quality=85, optimize=True)
    return out.getvalue()


@app.post("/api/bookings")
async def create_booking(request: Request, payload: str = Form(...), screenshot: UploadFile = File(...),
                         user: dict = Depends(current_user)):
    st = hours.status()
    if st["offline"]:
        return JSONResponse({"error": "offline", "hours": st}, status_code=403)
    raw = await screenshot.read(MAX_UPLOAD + 1)
    try:
        if not raw or len(raw) > MAX_UPLOAD:
            raise bookings.BookingError({"screenshot": "invalid"})
        image = _prepare_image(raw)
        clean = bookings.parse_and_validate(payload)
    except bookings.BookingError as e:
        return JSONResponse({"error": "validation", "errors": e.errors}, status_code=e.status)

    key = bookings.dedupe_key(user["id"], payload, image)
    prior = bookings.seen_recently(key)
    if prior:  # double tap / retry: don't notify admins twice
        return {"ref": prior, "duplicate": True, "pdf_sent": True}

    if bookings.rate_limited(user["id"]):  # only real, new bookings count (not validation retries or duplicates)
        return JSONResponse({"error": "rate_limited"}, status_code=429)
    rec = bookings.build_record(clean, user)
    pdf_bytes = pdf.build_pdf(rec)

    if config.DEV_MODE:
        DEV_OUT.mkdir(exist_ok=True)
        (DEV_OUT / f"{rec['ref']}.pdf").write_bytes(pdf_bytes)
        (DEV_OUT / f"{rec['ref']}.jpg").write_bytes(image)
        (DEV_OUT / f"{rec['ref']}.txt").write_text(notify.admin_text(rec), encoding="utf-8")
        result = {"admins_ok": 1, "client_ok": True}
    else:
        result = await notify.send_booking(request.app.state.ptb.bot, rec, image, pdf_bytes)
        if result["admins_ok"] == 0:
            log.error("booking %s reached NO admin", rec["ref"])
            return JSONResponse({"error": "delivery_failed"}, status_code=502)
    bookings.remember(key, rec["ref"])
    log.info("booking %s created (admins %s/%s)", rec["ref"], result["admins_ok"], len(config.ADMIN_IDS))
    return {"ref": rec["ref"], "service": rec["service"], "price": rec["price"], "deposit": rec["deposit"],
            "pdf_sent": result["client_ok"]}


@app.post("/api/catalog")
async def send_catalog(request: Request, user: dict = Depends(current_user)):
    """Same as the bot's 'Services Catalog' button: send the PDF into the user's chat."""
    if config.DEV_MODE:
        return {"sent": config.CATALOG_PATH.exists()}
    bot = request.app.state.ptb.bot
    s = catalog.strings()
    if config.CATALOG_PATH.exists():
        await bot.send_document(user["id"], document=InputFile(config.CATALOG_PATH.read_bytes(), filename="AGOS_Services_Catalog.pdf"),
                                caption=s["catalog_caption"])
        return {"sent": True}
    await bot.send_message(user["id"], s["catalog_missing"])
    return {"sent": False}


@app.post(f"/{config.WEBHOOK_PATH}")
async def telegram_webhook(request: Request, x_telegram_bot_api_secret_token: str = Header(default="")):
    if config.WEBHOOK_SECRET_TOKEN and x_telegram_bot_api_secret_token != config.WEBHOOK_SECRET_TOKEN:
        raise HTTPException(403)
    ptb = request.app.state.ptb
    if not ptb:
        raise HTTPException(503)
    await ptb.process_update(Update.de_json(await request.json(), ptb.bot))
    return {"ok": True}


class NoCacheStatic(StaticFiles):
    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        resp.headers["Cache-Control"] = "no-cache"
        return resp


@app.get("/")
async def root():
    return RedirectResponse("/app/")


app.mount("/app", NoCacheStatic(directory=str(config.WEBAPP_DIR), html=True), name="webapp")
