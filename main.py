"""
Main entry point for the Quran Telegram Bot.
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application

import database
from bot import setup_bot
from scheduler import setup_scheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot."""
    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    timezone = os.getenv("TIMEZONE", "America/New_York")
    send_hour = int(os.getenv("SEND_HOUR", "19"))
    send_minute = int(os.getenv("SEND_MINUTE", "0"))

    # Validate required variables
    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return

    if not openai_api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return

    logger.info("Starting Quran Telegram Bot...")

    # Initialize database
    database.init_db()

    # Create application
    application = Application.builder().token(telegram_token).build()

    # Set up bot handlers
    setup_bot(application)

    # Set up scheduler
    scheduler = setup_scheduler(
        application.bot,
        timezone,
        send_hour,
        send_minute
    )
    scheduler.start()

    logger.info(f"Bot started successfully! Daily verses scheduled for {send_hour:02d}:{send_minute:02d} {timezone}")

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
