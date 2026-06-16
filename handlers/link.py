"""
/link handler

Allows a user to manually link their Telegram account to their UwU Apps
account by entering their username or email.

Flow:
  1. /link                  — check if already linked; prompt for identifier
  2. User sends identifier  — look up in Supabase; confirm and save link
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from db import (
    get_link_by_telegram,
    get_link_by_uwu_user,
    upsert_link,
    set_link_state,
    get_link_state,
    clear_link_state,
)
from supabase_client import find_uwu_user_by_identifier

logger = logging.getLogger(__name__)

STEP_WAITING_IDENTIFIER = "waiting_identifier"


async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    existing = get_link_by_telegram(user.id)
    if existing:
        display = existing["uwu_display_name"] or existing["uwu_username"]
        await update.message.reply_text(
            f"✅ Your Telegram is already linked to UwU Apps.\n\n"
            f"👤 Account: {display} (@{existing['uwu_username']})\n"
            f"📧 Email: {existing['uwu_email']}\n\n"
            "Use /unlink if you want to remove this link."
        )
        return

    set_link_state(user.id, STEP_WAITING_IDENTIFIER)
    await update.message.reply_text(
        "🔗 Let's link your Telegram to your UwU Apps account.\n\n"
        "Please send your UwU Apps username or email address:"
    )


async def link_step_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles free-text messages during the /link conversation."""
    user = update.effective_user
    state = get_link_state(user.id)

    if not state or state["step"] != STEP_WAITING_IDENTIFIER:
        # Not in a link flow — ignore
        return

    identifier = update.message.text.strip()
    if not identifier:
        await update.message.reply_text("Please send your UwU Apps username or email address.")
        return

    # Look up user in Supabase
    uwu_user = find_uwu_user_by_identifier(identifier)
    if not uwu_user:
        await update.message.reply_text(
            "❌ No UwU Apps account found with that username or email.\n\n"
            "Please check and try again, or send /link to restart."
        )
        return

    # Check if this UwU account is already linked to another Telegram
    existing_uwu_link = get_link_by_uwu_user(uwu_user["id"])
    if existing_uwu_link and existing_uwu_link["telegram_id"] != user.id:
        clear_link_state(user.id)
        await update.message.reply_text(
            "⚠️ That UwU Apps account is already linked to a different Telegram account.\n\n"
            "Each UwU Apps account can only be linked to one Telegram account.\n"
            "Please use the correct Telegram account, or contact support."
        )
        return

    # Save the link
    upsert_link(
        telegram_id=user.id,
        telegram_username=user.username or "",
        uwu_user_id=uwu_user["id"],
        uwu_username=uwu_user["username"],
        uwu_email=uwu_user["email"],
        uwu_display_name=uwu_user.get("display_name") or "",
    )
    clear_link_state(user.id)

    display = uwu_user.get("display_name") or uwu_user["username"]
    await update.message.reply_text(
        f"🎉 Linked successfully!\n\n"
        f"👤 Account: {display} (@{uwu_user['username']})\n"
        f"📧 Email: {uwu_user['email']}\n\n"
        "You can now use \"Login with Telegram\" on any UwU App.\n"
        "Use /unlink to remove this link at any time."
    )