"""
/login handler — bot-initiated OTP flow

The user sends /login (optionally with an app_id argument) from Telegram.
The bot generates a 6-digit OTP, stores it in uwutele_otps, and replies
with it. The user then types this OTP into the web app's login form.
The web app verifies it against the DB and logs the user in.

Usage:
  /login              — generates OTP for the default app (uwuapps)
  /login mrt-app      — generates OTP scoped to a specific app_id

Web app verification endpoint should call get_valid_otp(otp) and, if valid,
mark it used with mark_otp_used(otp) and log the session.
"""

import logging
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import (
    get_link_by_telegram,
    insert_otp,
    get_active_otp_for_user,
    purge_expired_otps,
    persist_button,
)
from config import TOKEN_EXPIRY_SECONDS

logger = logging.getLogger(__name__)

OTP_LENGTH = 6


def _generate_otp() -> str:
    """Generate a 6-digit numeric OTP."""
    return "".join(random.choices(string.digits, k=OTP_LENGTH))


async def login_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Must be linked first
    link = get_link_by_telegram(user.id)
    if not link:
        await update.message.reply_text(
            "⚠️ Your Telegram is not linked to any UwU Apps account yet.\n\n"
            "Use /link to connect your account first, then use /login to get a login code."
        )
        return

    purge_expired_otps()

    # Check for an already-active OTP
    existing = get_active_otp_for_user(user.id)
    if existing:
        otp = existing["otp"]
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Generate new code", callback_data=f"login_refresh"),
        ]])
        msg = await update.message.reply_text(
            f"🔑 You already have an active login code:\n\n"
            f"<code>{otp}</code>\n\n"
            f"Enter this code in the UwU App login form.\n"
            f"It expires in {TOKEN_EXPIRY_SECONDS // 60} minutes and is single-use.\n\n"
            "Need a fresh code instead?",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        persist_button(str(msg.message_id), update.effective_chat.id, "login_refresh", "login")
        return

    # Determine app_id from optional argument
    app_id = context.args[0].strip() if context.args else "uwuapps"

    otp = _generate_otp()
    insert_otp(
        otp=otp,
        telegram_id=user.id,
        uwu_user_id=link["uwu_user_id"],
        app_id=app_id,
        expiry_seconds=TOKEN_EXPIRY_SECONDS,
    )

    display = link["uwu_display_name"] or link["uwu_username"]

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Generate new code", callback_data="login_refresh"),
    ]])

    msg = await update.message.reply_text(
        f"🔑 Your login code:\n\n"
        f"<code>{otp}</code>\n\n"
        f"👤 Account: {display} (@{link['uwu_username']})\n\n"
        "Enter this code in the UwU App login form.\n"
        f"It expires in {TOKEN_EXPIRY_SECONDS // 60} minutes and is single-use.",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    persist_button(str(msg.message_id), update.effective_chat.id, "login_refresh", "login")


async def login_refresh_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for the 'Generate new code' button — invalidates old OTP and issues a new one."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    link = get_link_by_telegram(user.id)

    if not link:
        await query.edit_message_text(
            "⚠️ Your account is no longer linked. Use /link to reconnect."
        )
        return

    purge_expired_otps()

    # Invalidate any existing active OTP by marking it used
    from db import get_active_otp_for_user, mark_otp_used
    existing = get_active_otp_for_user(user.id)
    if existing:
        mark_otp_used(existing["otp"])

    otp = _generate_otp()
    insert_otp(
        otp=otp,
        telegram_id=user.id,
        uwu_user_id=link["uwu_user_id"],
        app_id="uwuapps",
        expiry_seconds=TOKEN_EXPIRY_SECONDS,
    )

    display = link["uwu_display_name"] or link["uwu_username"]

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Generate new code", callback_data="login_refresh"),
    ]])

    await query.edit_message_text(
        f"🔑 Your new login code:\n\n"
        f"<code>{otp}</code>\n\n"
        f"👤 Account: {display} (@{link['uwu_username']})\n\n"
        "Enter this code in the UwU App login form.\n"
        f"It expires in {TOKEN_EXPIRY_SECONDS // 60} minutes and is single-use.",
        parse_mode="HTML",
        reply_markup=keyboard,
    )

    # Re-persist button for new message state
    persist_button(
        str(query.message.message_id),
        query.message.chat.id,
        "login_refresh",
        "login",
    )