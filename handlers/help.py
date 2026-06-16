"""
/help handler
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ UwU Apps 2FA Bot — Help\n\n"
        "This bot lets you log in to UwU Apps using your Telegram account "
        "instead of (or in addition to) a password.\n\n"
        "📌 Commands:\n"
        "  /login   — Get a one-time code to type into a UwU App\n"
        "  /link    — Connect your Telegram to your UwU Apps account\n"
        "  /unlink  — Disconnect from your UwU Apps account\n"
        "  /status  — View your current link status\n"
        "  /help    — Show this message\n\n"
        "🔐 Login via deep link (web app initiates):\n"
        "1. Open any UwU App in your browser.\n"
        "2. Click \"Login with Telegram\".\n"
        "3. Telegram opens this bot with a unique link.\n"
        "4. If your account is linked, login is approved instantly.\n"
        "5. Return to the app — you are signed in.\n\n"
        "🔑 Login via OTP code (you initiate):\n"
        "1. Send /login here.\n"
        "2. The bot gives you a 6-digit code.\n"
        "3. Open any UwU App and choose \"Login with OTP\".\n"
        "4. Enter the code — you are signed in.\n\n"
        "🌐 UwU Apps: https://uwuapps.org\n"
        "📩 Support: support@uwuapps.org"
    )