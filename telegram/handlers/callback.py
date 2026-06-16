"""
Generic callback handler.

Routes callback_data to the correct handler function
using the uwutele_buttons persistence table.
This ensures inline buttons keep working after a bot restart.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from db import get_button_handler

logger = logging.getLogger(__name__)

# Map handler name -> callable
# Add new handlers here as the bot grows.
HANDLER_REGISTRY: dict = {}

# Populated after imports to avoid circular dependency
def _build_registry():
    from handlers.unlink import unlink_confirm_handler
    from handlers.login import login_refresh_handler
    HANDLER_REGISTRY["unlink"] = unlink_confirm_handler
    HANDLER_REGISTRY["login"]  = login_refresh_handler


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not HANDLER_REGISTRY:
        _build_registry()

    message_id = str(query.message.message_id)
    chat_id    = query.message.chat.id
    data       = query.data

    handler_name = get_button_handler(message_id, chat_id, data)

    if handler_name and handler_name in HANDLER_REGISTRY:
        await HANDLER_REGISTRY[handler_name](update, context)
    else:
        await query.answer("This button is no longer active.", show_alert=True)