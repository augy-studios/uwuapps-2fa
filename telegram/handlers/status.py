"""
/status handler

Shows the user's current link status, refreshing UwU Apps profile data
from Supabase so it's always up to date.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from db import get_link_by_telegram, upsert_link
from supabase_client import find_uwu_user_by_id

logger = logging.getLogger(__name__)


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    link = get_link_by_telegram(user.id)

    if not link:
        await update.message.reply_text(
            "🔴 Not linked\n\n"
            "Your Telegram is not linked to any UwU Apps account.\n"
            "Use /link to set one up."
        )
        return

    # Refresh from Supabase to ensure data is current
    uwu_user = find_uwu_user_by_id(link["uwu_user_id"])

    if not uwu_user:
        await update.message.reply_text(
            "⚠️ Your linked UwU Apps account no longer exists.\n\n"
            "Use /unlink to clear the stale link, then /link to connect a new account."
        )
        return

    # Keep cached data in sync
    upsert_link(
        telegram_id=user.id,
        telegram_username=user.username or "",
        uwu_user_id=uwu_user["id"],
        uwu_username=uwu_user["username"],
        uwu_email=uwu_user["email"],
        uwu_display_name=uwu_user.get("display_name") or "",
    )

    display = uwu_user.get("display_name") or uwu_user["username"]
    await update.message.reply_text(
        f"🟢 Linked\n\n"
        f"👤 Display name: {display}\n"
        f"🆔 Username: @{uwu_user['username']}\n"
        f"📧 Email: {uwu_user['email']}\n\n"
        "\"Login with Telegram\" is active on all UwU Apps.\n"
        "Use /unlink to remove this link."
    )