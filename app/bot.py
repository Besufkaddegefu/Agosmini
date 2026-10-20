"""Telegram bot: launcher for the Mini App + admin Confirm/Reject buttons."""
from __future__ import annotations
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, Update, WebAppInfo
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from . import catalog, config, hours, notify

log = logging.getLogger("agos.bot")
WEBAPP_VERSION = "1"  # bump to bust Telegram's WebView cache after a frontend release


def webapp_url() -> str:
    return f"{config.PUBLIC_BASE_URL}/app/?v={WEBAPP_VERSION}"


def open_keyboard() -> InlineKeyboardMarkup:
    # Must be an INLINE web_app button: reply-keyboard Web Apps do not receive initData.
    return InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Open Booking App / ለማዘዝ ይክፈቱ",
                                                       web_app=WebAppInfo(webapp_url()))]])


def check_again_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Check Again", callback_data="check_again")]])


async def _offline(update: Update) -> None:
    text = catalog.strings()["offline"].format(phone=config.CONTACT_PHONE)
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(text, reply_markup=check_again_keyboard(), parse_mode=ParseMode.MARKDOWN)


def welcome_text() -> str:
    ui = catalog.ui()
    first = lambda s: s.split("\n\n")[0].replace("*", "")  # noqa: E731
    return f"{first(ui['en']['welcome'])}\n{first(ui['am']['welcome'])}\n\n{catalog.strings()['welcome_choose']}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if hours.is_offline():
        return await _offline(update)
    await update.message.reply_text(welcome_text(), reply_markup=open_keyboard())


async def check_again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if hours.is_offline():
        return await _offline(update)
    await q.message.reply_text(welcome_text(), reply_markup=open_keyboard())


async def decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in config.ADMIN_IDS:
        return await q.answer("Admins only", show_alert=True)
    action, ref, uid = q.data.split(":", 2)
    note = await notify.decide(context.bot, action, ref, int(uid), q.from_user.first_name or "admin", q.message)
    await q.answer(note)


def build_application() -> Application:
    app = Application.builder().token(config.BOT_TOKEN).updater(None).build()
    app.add_handler(CommandHandler(["start", "menu"], start))
    app.add_handler(CallbackQueryHandler(check_again, pattern="^check_again$"))
    app.add_handler(CallbackQueryHandler(decision, pattern=r"^(cfm|rej):"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, start))
    return app


async def configure(app: Application) -> None:
    """Register the webhook and the chat menu button that opens the Mini App."""
    if not config.PUBLIC_BASE_URL:
        log.warning("PUBLIC_BASE_URL not set - webhook and menu button not configured")
        return
    await app.bot.set_webhook(url=f"{config.PUBLIC_BASE_URL}/{config.WEBHOOK_PATH}",
                              secret_token=config.WEBHOOK_SECRET_TOKEN,
                              allowed_updates=["message", "callback_query"], drop_pending_updates=True)
    await app.bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="Book / ያዝዙ", web_app=WebAppInfo(webapp_url())))
