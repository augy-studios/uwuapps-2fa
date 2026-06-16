"""
UwU Apps 2FA Bot — @uwuapps_2fa_bot
Handles Telegram-based login (2FA) for UwU Apps users.
"""

import logging
import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from handlers.start import start_handler
from handlers.link import link_handler, link_step_handler
from handlers.unlink import unlink_handler, unlink_confirm_handler
from handlers.status import status_handler
from handlers.help import help_handler
from handlers.login import login_handler
from handlers.callback import callback_handler

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application):
    await application.bot.set_my_commands([
        ("start",  "Start or process a login request"),
        ("login",  "Get a one-time login code to enter in a UwU App"),
        ("link",   "Link your Telegram to your UwU Apps account"),
        ("unlink", "Unlink your Telegram from your UwU Apps account"),
        ("status", "Check your link status"),
        ("help",   "Show help information"),
    ])


def main():
    logger.info("Starting UwU Apps 2FA Bot...")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start",  start_handler))
    app.add_handler(CommandHandler("login",  login_handler))
    app.add_handler(CommandHandler("link",   link_handler))
    app.add_handler(CommandHandler("unlink", unlink_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("help",   help_handler))
    app.add_handler(CallbackQueryHandler(unlink_confirm_handler, pattern="^unlink_"))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, link_step_handler))

    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()