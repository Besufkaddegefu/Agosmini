"""Single place for all settings. Same env var names as the original bot."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "app" / "data"
WEBAPP_DIR = BASE_DIR / "webapp"
FONT_DIR = BASE_DIR / "app" / "fonts"

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PUBLIC_BASE_URL = (os.environ.get("PUBLIC_BASE_URL")
                   or os.environ.get("RENDER_EXTERNAL_URL")
                   or os.environ.get("WEBHOOK_BASE_URL") or "").rstrip("/")
WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH", "agos-bot").strip("/")
WEBHOOK_SECRET_TOKEN = os.environ.get("WEBHOOK_SECRET_TOKEN") or None
PORT = int(os.environ.get("PORT", "10000"))

ADMIN_IDS = [int(v) for v in (os.environ.get(f"ADMIN_ID_{i}") for i in (1, 2, 3)) if v]

# Hours when the service is OFFLINE (customers should call). Standard 24h clock,
# Africa/Addis_Ababa. 08:00-20:00 here == 2:00 AM - 2:00 PM on the Ethiopian clock.
TIMEZONE = "Africa/Addis_Ababa"
OFFLINE_START_HOUR = int(os.environ.get("OFFLINE_START_HOUR", "8"))
OFFLINE_END_HOUR = int(os.environ.get("OFFLINE_END_HOUR", "20"))

# Payment (defaults from the original bot; override with env vars)
BANK_NAME = os.environ.get("BANK_NAME", "Commercial Bank of Ethiopia (CBE)")
BANK_ACCOUNT_NAME = os.environ.get("BANK_ACCOUNT_NAME", "Sara Mohammed")
BANK_ACCOUNT_NUMBER = os.environ.get("BANK_ACCOUNT_NUMBER", "1000505694407")
DEPOSIT_PERCENT = 50

# Contact details
CONTACT_PHONE = "+251 967 621 545"
CONTACT_PHONES = ["+251 967 621 545", "+251 980 040 468"]
WEBSITE = "www.agospostpartumcare.com"
EMAIL = "info@agospostpartumcare.com"

LOGO_PATH = Path(os.environ.get("LOGO_PATH", str(WEBAPP_DIR / "assets" / "logo.webp")))
CATALOG_PATH = Path(os.environ.get("SERVICES_PDF_PATH", str(WEBAPP_DIR / "assets" / "services_catalog.pdf")))

# Local development only: DEV_MODE=1 accepts an unsigned X-Dev-User header and
# never contacts Telegram. Leave unset in production.
DEV_MODE = os.environ.get("DEV_MODE") == "1"
