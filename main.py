"""
Main entry point for the Quran Telegram Bot.
"""

import os
import json
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application

import database
import quran_service
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
    timezone = os.getenv("TIMEZONE", "America/New_York")
    send_hour = int(os.getenv("SEND_HOUR", "19"))
    send_minute = int(os.getenv("SEND_MINUTE", "0"))

    # Validate required variables
    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return

    logger.info("Starting Quran Telegram Bot...")

    # Load Quran translation data
    logger.info("Loading Quran translation data...")
    try:
        json_path = "quran_en.json"
        with open(json_path, "r", encoding="utf-8") as f:
            quran_translations = json.load(f)

        # Validate structure
        if not isinstance(quran_translations, list) or len(quran_translations) != 114:
            logger.error(f"Invalid quran_en.json structure: expected 114 surahs, got {len(quran_translations)}")
            return

        logger.info(f"Successfully loaded {len(quran_translations)} surahs")

        # Store in quran_service
        quran_service.set_translations(quran_translations)

    except FileNotFoundError:
        logger.error(f"quran_en.json not found in {os.getcwd()}")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in quran_en.json: {e}")
        return
    except Exception as e:
        logger.error(f"Error loading translations: {e}")
        return

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
