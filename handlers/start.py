"""
/start handler

Two modes:
  1. /start              — welcome message
  2. /start <TOKEN>      — process a login token from a web app deep link
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from db import (
    get_valid_token,
    mark_token_used,
    record_session,
    get_link_by_telegram,
    get_link_by_uwu_user,
    upsert_link,
    purge_expired_tokens,
)
from supabase_client import find_uwu_user_by_id

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    # ── Plain /start ────────────────────────────────────────────────────────
    if not args:
        await update.message.reply_text(
            f"👋 Hi {user.first_name}!\n\n"
            "I handle Telegram-based login for UwU Apps.\n\n"
            "📌 Commands:\n"
            "  /link — Link your Telegram to your UwU Apps account\n"
            "  /unlink — Remove the link\n"
            "  /status — Check your link status\n"
            "  /help — More information\n\n"
            "To log in to a UwU App via Telegram, click the "
            "\"Login with Telegram\" button inside the app."
        )
        return

    # ── Deep-link login: /start <TOKEN> ─────────────────────────────────────
    token_str = args[0].strip()

    purge_expired_tokens()
    token_row = get_valid_token(token_str)

    if not token_row:
        await update.message.reply_text(
            "❌ This login link is invalid or has expired.\n\n"
            "Please request a new login link from the app."
        )
        return

    uwu_user_id = token_row["uwu_user_id"]
    app_label   = token_row["app_label"]
    app_id      = token_row["app_id"]

    # Fetch the latest user data from Supabase
    uwu_user = find_uwu_user_by_id(uwu_user_id)
    if not uwu_user:
        await update.message.reply_text(
            "❌ The UwU Apps account linked to this login request no longer exists.\n\n"
            "Please contact support."
        )
        return

    # Check existing link for THIS Telegram account
    tg_link = get_link_by_telegram(user.id)

    if tg_link:
        # This Telegram account is already linked — check if it matches the requesting user
        if tg_link["uwu_user_id"] != uwu_user_id:
            await update.message.reply_text(
                "⚠️ Your Telegram account is currently linked to a different UwU Apps account "
                f"(@{tg_link['uwu_username']}).\n\n"
                "If you want to log in as a different user, please /unlink first."
            )
            return

        # Same user — update cached profile data from Supabase and approve login
        upsert_link(
            telegram_id=user.id,
            telegram_username=user.username or "",
            uwu_user_id=uwu_user["id"],
            uwu_username=uwu_user["username"],
            uwu_email=uwu_user["email"],
            uwu_display_name=uwu_user.get("display_name") or "",
        )
        mark_token_used(token_str)
        record_session(token_str, user.id, uwu_user_id, app_id)

        display = uwu_user.get("display_name") or uwu_user["username"]
        await update.message.reply_text(
            f"✅ Login approved!\n\n"
            f"🌐 App: {app_label}\n"
            f"👤 Logged in as: {display} (@{uwu_user['username']})\n\n"
            "You can return to the app — you are now logged in."
        )
        return

    # Check if the UwU account is linked to a DIFFERENT Telegram account
    uwu_link = get_link_by_uwu_user(uwu_user_id)
    if uwu_link and uwu_link["telegram_id"] != user.id:
        await update.message.reply_text(
            "⚠️ This UwU Apps account is already linked to a different Telegram account.\n\n"
            "Each UwU Apps account can only be linked to one Telegram account at a time.\n"
            "Please use the Telegram account that was originally linked, or unlink it first."
        )
        return

    # Not yet linked — link now and approve the login in one step
    upsert_link(
        telegram_id=user.id,
        telegram_username=user.username or "",
        uwu_user_id=uwu_user["id"],
        uwu_username=uwu_user["username"],
        uwu_email=uwu_user["email"],
        uwu_display_name=uwu_user.get("display_name") or "",
    )
    mark_token_used(token_str)
    record_session(token_str, user.id, uwu_user_id, app_id)

    display = uwu_user.get("display_name") or uwu_user["username"]
    await update.message.reply_text(
        f"🎉 Your Telegram account has been linked to UwU Apps and your login is approved!\n\n"
        f"🌐 App: {app_label}\n"
        f"👤 Logged in as: {display} (@{uwu_user['username']})\n\n"
        "You can return to the app — you are now logged in.\n\n"
        "ℹ️ Future logins from any UwU App will be approved automatically via this chat."
    )