"""
/unlink handler

Removes the Telegram <-> UwU Apps link after confirmation via inline button.
The confirmation button is persisted in SQLite so it survives bot restarts.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import (
    get_link_by_telegram,
    delete_link,
    clear_link_state,
    persist_button,
)

logger = logging.getLogger(__name__)


async def unlink_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    existing = get_link_by_telegram(user.id)
    if not existing:
        await update.message.reply_text(
            "ℹ️ Your Telegram is not currently linked to any UwU Apps account.\n\n"
            "Use /link to link one."
        )
        return

    display = existing["uwu_display_name"] or existing["uwu_username"]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, unlink", callback_data="unlink_confirm"),
            InlineKeyboardButton("❌ Cancel",      callback_data="unlink_cancel"),
        ]
    ])

    msg = await update.message.reply_text(
        f"⚠️ Are you sure you want to unlink your Telegram from:\n\n"
        f"👤 {display} (@{existing['uwu_username']})\n"
        f"📧 {existing['uwu_email']}\n\n"
        "You will need to re-link to use \"Login with Telegram\" again.",
        reply_markup=keyboard,
    )

    # Persist buttons so they survive a bot restart
    for data in ("unlink_confirm", "unlink_cancel"):
        persist_button(
            message_id=str(msg.message_id),
            chat_id=update.effective_chat.id,
            button_data=data,
            handler="unlink",
        )


async def unlink_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user

    if query.data == "unlink_cancel":
        await query.edit_message_text("↩️ Unlink cancelled. Your account remains linked.")
        return

    if query.data == "unlink_confirm":
        existing = get_link_by_telegram(user.id)
        if not existing:
            await query.edit_message_text(
                "ℹ️ Your Telegram was not linked to any account (nothing to unlink)."
            )
            return

        delete_link(user.id)
        clear_link_state(user.id)

        await query.edit_message_text(
            "🔓 Your Telegram has been unlinked from UwU Apps.\n\n"
            "Use /link to link a new account."
        )