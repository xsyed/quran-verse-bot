"""
Telegram bot handlers and commands.
"""

import logging
import os
import pytz
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import database
from quran_data import get_surah_info

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - Subscribe user to daily verses."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    is_new_user = database.add_user(user_id, chat_id)

    if is_new_user:
        welcome_message = (
            "🌙 Assalamu Alaikum! Welcome to the Daily Quran Bot.\n\n"
            "You will receive 3 verses from the Quran every day at 7:00 PM EST, "
            "starting from Surah Al-Fatihah (1:1).\n\n"
            "Each verse includes:\n"
            "• Transliteration\n"
            "• English Translation\n"
            "• Context and Understanding\n\n"
            "Your journey through the Quran begins now!\n\n"
            "Commands:\n"
            "/start - Subscribe to daily verses\n"
            "/stop - Unsubscribe from daily verses\n"
            "/anotherone - Get next 3 verses on demand (max 10/day)"
        )
    else:
        progress = database.get_user_progress(user_id)
        if progress:
            surah, verse = progress
            surah_info = get_surah_info(surah)
            surah_name = surah_info["name"] if surah_info else "Unknown"
            welcome_message = (
                f"🌙 Welcome back!\n\n"
                f"You have been resubscribed to daily verses.\n"
                f"Your current progress: Surah {surah}:{verse} ({surah_name})\n\n"
                f"You will receive your next verses at 7:00 PM EST."
            )
        else:
            welcome_message = "Welcome back! You have been resubscribed to daily verses."

    await update.message.reply_text(welcome_message)
    logger.info(f"User {user_id} subscribed (new: {is_new_user})")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command - Unsubscribe user from daily verses."""
    user_id = update.effective_user.id

    success = database.deactivate_user(user_id)

    if success:
        message = (
            "You have been unsubscribed from daily verses.\n\n"
            "Your progress has been saved. Use /start anytime to resume."
        )
    else:
        message = "You were not subscribed."

    await update.message.reply_text(message)
    logger.info(f"User {user_id} unsubscribed")


async def anotherone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /anotherone command - Send next 3 verses on demand."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Get timezone from environment
    timezone_str = os.getenv("TIMEZONE", "America/New_York")

    # Check if user exists and is active
    progress = database.get_user_progress(user_id)
    if not progress:
        await update.message.reply_text(
            "You are not subscribed to daily verses.\n\n"
            "Please use /start to subscribe first."
        )
        logger.info(f"User {user_id} tried /anotherone but is not subscribed")
        return

    # Check if user has requests remaining today
    if not database.can_request_verses(user_id, timezone_str):
        # Calculate when the limit resets (midnight EST)
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
        # Add one day
        from datetime import timedelta
        tomorrow = tomorrow + timedelta(days=1)

        await update.message.reply_text(
            "You have reached your daily limit of 10 verse requests.\n\n"
            f"Your limit will reset at midnight EST.\n\n"
            "See you tomorrow!"
        )
        logger.info(f"User {user_id} hit daily request limit")
        return

    # Get current progress
    current_surah, current_verse = progress

    # Import the send_three_verses_to_user function
    from scheduler import send_three_verses_to_user

    # Send the verses
    success, final_surah, final_verse = await send_three_verses_to_user(
        context.bot, user_id, chat_id, current_surah, current_verse
    )

    if success:
        # Increment request count
        database.increment_request_count(user_id, timezone_str)
        logger.info(f"User {user_id} used /anotherone successfully")
    else:
        await update.message.reply_text(
            "Sorry, there was an error sending your verses. Please try again later."
        )
        logger.error(f"Failed to send verses for user {user_id} via /anotherone")


def setup_bot(application: Application):
    """Set up bot command handlers."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("anotherone", anotherone_command))

    logger.info("Bot handlers registered")
