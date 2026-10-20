"""Deliver a booking to admins (photo + details + PDF + Confirm/Reject) and to the client."""
from __future__ import annotations
import asyncio, html, logging, re

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError

from . import catalog, config

log = logging.getLogger("agos.notify")
CAPTION_LIMIT = 1024
# ref -> {"msgs": [(chat_id, message_id, is_caption)], "state": None | "cfm" | "rej"}
# In-memory, best effort: lets one admin's decision update the other admins' copies.
REGISTRY: dict = {}

DECISION_TEXT = {
    "cfm": "✅ Your booking {ref} has been confirmed! Our team will contact you shortly.\n"
           "✅ ትዕዛዝዎ {ref} ተረጋግጧል! ቡድናችን በቅርቡ ያነጋግርዎታል።",
    "rej": "❌ We could not verify your payment for booking {ref}. Please contact us: {phone}\n"
           "❌ ለትዕዛዝ {ref} ክፍያዎን ማረጋገጥ አልቻልንም። እባክዎ ያግኙን፦ {phone}",
}


def _e(v) -> str:
    return html.escape(str(v), quote=False)


def safe_filename(s: str) -> str:
    return re.sub(r"[^\w\-.\u1200-\u137F]+", "_", s).strip("_")[:40] or "Booking"


def admin_text(rec: dict) -> str:
    form, v, c = rec["form"], rec["values"], rec["created"]
    line = "━" * 39
    out = [form["admin_title"], line, "",
           f"<b>Booking Reference:</b> {_e(rec['ref'])}",
           f"<b>Booking Date:</b> {c.strftime('%B %d, %Y')}",
           f"<b>Booking Time:</b> {c.strftime('%H:%M:%S')}", ""]
    for title, fields in form["admin_rows"]:
        out.append(f"<b>{_e(title)}</b>")
        for label, key in fields:
            if key in ("alt_phone", "house", "gender") and v[key] == "-":
                continue
            out.append(f"   • {_e(label)}: {_e(v[key])}")
        out.append("")
    out += ["<b>3. PAYMENT INFORMATION</b>",
            f"   • Bank: {_e(config.BANK_NAME)}",
            f"   • Account Name: {_e(config.BANK_ACCOUNT_NAME)}",
            f"   • Account Number: {_e(config.BANK_ACCOUNT_NUMBER)}",
            f"   • Package Price: {catalog.money(rec['price'])}",
            f"   • Required Deposit ({config.DEPOSIT_PERCENT}%): {catalog.money(rec['deposit'])}",
            "   • Status: PENDING - Payment Screenshot Received, Awaiting Verification", "", line,
            "✅ Payment screenshot has been received.",
            "⚠️ Please verify the payment and confirm the booking by contacting the client.",
            f"📱 Client Phone: {_e(v['phone'])}",
            f"📱 Client Telegram: {_e(v['username'])}"]
    return "\n".join(out)


def admin_keyboard(rec: dict, with_user_link: bool = True) -> InlineKeyboardMarkup:
    uid, ref = rec["user"]["id"], rec["ref"]
    rows = [[InlineKeyboardButton("✅ Confirm payment", callback_data=f"cfm:{ref}:{uid}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"rej:{ref}:{uid}")]]
    uname = (rec["values"]["username"] or "").lstrip("@")
    if uname and uname != "-":
        rows.append([InlineKeyboardButton("💬 Message client", url=f"https://t.me/{uname}")])
    elif with_user_link:
        rows.append([InlineKeyboardButton("💬 Message client", url=f"tg://user?id={uid}")])
    return InlineKeyboardMarkup(rows)


async def _send_to_admin(bot: Bot, admin_id: int, rec: dict, image: bytes, pdf: bytes) -> bool:
    text = admin_text(rec)
    msgs = []
    try:
        long = len(text) > CAPTION_LIMIT
        caption = f"🔔 {rec['ref']} - {rec['values']['name']}\n(details below)" if long else text

        async def photo(markup):
            return await bot.send_photo(admin_id, photo=image, caption=caption, parse_mode=ParseMode.HTML,
                                        reply_markup=None if long else markup)
        try:
            m1 = await photo(admin_keyboard(rec))
        except BadRequest as e:
            if "PRIVACY" not in str(e).upper():
                raise
            m1 = await photo(admin_keyboard(rec, with_user_link=False))
        msgs.append((admin_id, m1.message_id, True))
        if long:
            m2 = await bot.send_message(admin_id, text, parse_mode=ParseMode.HTML, reply_markup=admin_keyboard(rec, False))
            msgs.append((admin_id, m2.message_id, False))
    except TelegramError as e:
        log.warning("admin %s photo/summary failed: %s", admin_id, e)
        return False
    REGISTRY.setdefault(rec["ref"], {"msgs": [], "state": None})["msgs"].extend(msgs)
    try:
        name = f"{rec['form']['file_prefix']}_{safe_filename(rec['values']['name'])}.pdf"
        await bot.send_document(admin_id, document=InputFile(pdf, filename=name))
    except TelegramError as e:
        log.warning("admin %s pdf failed: %s", admin_id, e)
    return True


async def send_booking(bot: Bot, rec: dict, image: bytes, pdf: bytes) -> dict:
    results = await asyncio.gather(*(_send_to_admin(bot, a, rec, image, pdf) for a in config.ADMIN_IDS))
    client_ok = True
    try:
        await bot.send_document(rec["user"]["id"], document=InputFile(pdf, filename=rec["form"]["client_file"]),
                                caption=catalog.strings()["client_caption"])
    except TelegramError as e:
        client_ok = False
        log.warning("client %s pdf failed: %s", rec["user"]["id"], e)
    return {"admins_ok": sum(results), "admins_total": len(results), "client_ok": client_ok}


async def decide(bot: Bot, action: str, ref: str, client_id: int, admin_name: str, pressed) -> str:
    """Handle Confirm/Reject. Returns a short status line shown to the admin."""
    entry = REGISTRY.setdefault(ref, {"msgs": [], "state": None})
    if entry["state"]:
        return f"Already {'confirmed' if entry['state'] == 'cfm' else 'rejected'}"
    entry["state"] = action
    try:
        await bot.send_message(client_id, DECISION_TEXT[action].format(ref=ref, phone=config.CONTACT_PHONE))
        delivered = True
    except TelegramError as e:
        log.warning("could not notify client %s: %s", client_id, e)
        delivered = False
    status = ("✅ <b>CONFIRMED</b>" if action == "cfm" else "❌ <b>REJECTED</b>") + f" by {_e(admin_name)}"
    if not delivered:
        status += "\n⚠️ Client could not be notified automatically - please contact them."
    targets = list(entry["msgs"])
    if pressed is not None and not any((c, m) == (pressed.chat_id, pressed.message_id) for c, m, _ in targets):
        targets.append((pressed.chat_id, pressed.message_id, bool(pressed.caption)))
    for chat_id, mid, is_caption in targets:
        is_pressed = pressed is not None and (chat_id, mid) == (pressed.chat_id, pressed.message_id)
        try:
            if is_caption and is_pressed:
                await bot.edit_message_caption(chat_id, mid, caption=f"{pressed.caption_html}\n\n{status}", parse_mode=ParseMode.HTML)
            elif not is_caption and is_pressed:
                await bot.edit_message_text(f"{pressed.text_html}\n\n{status}", chat_id=chat_id, message_id=mid, parse_mode=ParseMode.HTML)
            else:
                await bot.edit_message_reply_markup(chat_id, mid, reply_markup=None)
        except TelegramError as e:
            log.info("edit failed for %s/%s: %s", chat_id, mid, e)
    return "Confirmed - client notified" if action == "cfm" else "Rejected - client notified"
