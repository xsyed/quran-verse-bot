"""
Daily scheduler for sending verses at 7:00 PM EST.
"""

import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from telegram import Bot
from telegram.error import TelegramError

import database
from quran_data import get_surah_info, get_next_verse
from openai_service import generate_three_verses_explanation, format_three_verses_message

logger = logging.getLogger(__name__)


async def send_three_verses_to_user(
    bot: Bot,
    user_id: int,
    chat_id: int,
    current_surah: int,
    current_verse: int
) -> tuple[bool, int, int]:
    """
    Send 3 verses to a specific user.
    This is a reusable function that can be called by both scheduled and on-demand requests.

    Args:
        bot: Telegram bot instance
        user_id: User ID
        chat_id: Chat ID
        current_surah: Starting surah number
        current_verse: Starting verse number

    Returns:
        Tuple of (success: bool, final_surah: int, final_verse: int)
    """
    try:
        logger.info(f"Sending verses to user {user_id} starting from {current_surah}:{current_verse}")

        # Collect data for 3 verses
        verses_data = []
        surah = current_surah
        verse = current_verse

        for i in range(3):
            # Get surah info
            surah_info = get_surah_info(surah)
            if not surah_info:
                logger.error(f"Invalid surah {surah} for user {user_id}")
                break

            verses_data.append({
                'surah': surah,
                'surah_name': surah_info['name'],
                'verse': verse
            })

            # Move to next verse for the next iteration
            next_position = get_next_verse(surah, verse)
            if next_position:
                surah, verse = next_position
            else:
                # Reached end of Quran
                logger.info(f"User {user_id} will complete the Quran after these verses")
                break

        # Check if we collected any verses
        if not verses_data:
            logger.error(f"No verses collected for user {user_id}")
            return False, current_surah, current_verse

        # Generate explanations for all verses in a single API call
        explanations = generate_three_verses_explanation(verses_data)

        if not explanations:
            logger.error(f"Failed to generate explanations for user {user_id}")
            return False, current_surah, current_verse

        # Format all verses into one message
        message = format_three_verses_message(verses_data, explanations)

        if not message:
            logger.error(f"Failed to format message for user {user_id}")
            return False, current_surah, current_verse

        # Send the combined message
        try:
            await bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Sent {len(verses_data)} verses to user {user_id} in one message")

            # Update user's progress in database
            database.update_user_progress(user_id, surah, verse)
            logger.info(f"Updated user {user_id} progress to {surah}:{verse}")

            # Check if user completed the Quran
            if len(verses_data) < 3 and not get_next_verse(surah, verse):
                await bot.send_message(
                    chat_id=chat_id,
                    text="🎉 Congratulations! You have completed reading the entire Quran!\n\n"
                         "May Allah accept your efforts and grant you the blessings of His words."
                )

            return True, surah, verse

        except TelegramError as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
            return False, current_surah, current_verse

    except Exception as e:
        logger.error(f"Error sending verses to user {user_id}: {e}")
        return False, current_surah, current_verse


async def send_daily_verses(bot: Bot, timezone_str: str = "America/New_York"):
    """
    Send 3 verses to all active users based on their individual progress.
    All 3 verses are sent as a single combined message.
    Only sends if user hasn't received verses today.
    """
    logger.info("Starting daily verse distribution...")

    active_users = database.get_active_users()
    logger.info(f"Found {len(active_users)} active users")

    for user_id, chat_id, current_surah, current_verse in active_users:
        try:
            # Check if user can receive verses (respects daily limit)
            if not database.can_request_verses(user_id, timezone_str):
                logger.info(f"User {user_id} has reached daily request limit, skipping")
                continue

            # Send verses using the reusable function
            success, final_surah, final_verse = await send_three_verses_to_user(
                bot, user_id, chat_id, current_surah, current_verse
            )

            # Increment request count if successful
            if success:
                database.increment_request_count(user_id, timezone_str)

        except Exception as e:
            logger.error(f"Error processing user {user_id}: {e}")
            continue

    logger.info("Daily verse distribution completed")


def setup_scheduler(bot: Bot, timezone_str: str, hour: int, minute: int) -> AsyncIOScheduler:
    """
    Set up the daily scheduler.

    Args:
        bot: Telegram bot instance
        timezone_str: Timezone string (e.g., 'America/New_York')
        hour: Hour to send (24-hour format)
        minute: Minute to send

    Returns:
        Configured scheduler
    """
    scheduler = AsyncIOScheduler()
    timezone = pytz.timezone(timezone_str)

    # Schedule daily task
    trigger = CronTrigger(
        hour=hour,
        minute=minute,
        timezone=timezone
    )

    scheduler.add_job(
        send_daily_verses,
        trigger=trigger,
        args=[bot, timezone_str],  # Pass timezone_str to the function
        id="daily_verses",
        name="Send daily Quran verses",
        replace_existing=True
    )

    logger.info(f"Scheduler configured for {hour:02d}:{minute:02d} {timezone_str}")
    return scheduler
