"""
SQLite database operations for user progress tracking.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Tuple
import logging
import pytz

logger = logging.getLogger(__name__)

# Use data directory if it exists (Docker), otherwise use current directory
DATA_DIR = "/app/data" if os.path.exists("/app/data") else "."
DB_NAME = os.path.join(DATA_DIR, "quran.db")


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            chat_id INTEGER NOT NULL,
            current_surah INTEGER DEFAULT 1,
            current_verse INTEGER DEFAULT 1,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_sent_at TIMESTAMP,
            requests_today INTEGER DEFAULT 0,
            last_request_date DATE
        )
    """)

    # Add new columns to existing tables if they don't exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN requests_today INTEGER DEFAULT 0")
        logger.info("Added requests_today column")
    except sqlite3.OperationalError:
        # Column already exists
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_request_date DATE")
        logger.info("Added last_request_date column")
    except sqlite3.OperationalError:
        # Column already exists
        pass

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


def add_user(user_id: int, chat_id: int) -> bool:
    """
    Add a new user or reactivate an existing user.
    Returns True if new user, False if existing user was reactivated.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Check if user exists
        cursor.execute("SELECT id, active FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if result:
            # User exists, reactivate if inactive
            cursor.execute(
                "UPDATE users SET active = 1, chat_id = ? WHERE user_id = ?",
                (chat_id, user_id)
            )
            conn.commit()
            conn.close()
            return False
        else:
            # New user
            cursor.execute(
                """
                INSERT INTO users (user_id, chat_id, current_surah, current_verse, active)
                VALUES (?, ?, 1, 1, 1)
                """,
                (user_id, chat_id)
            )
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        logger.error(f"Error adding user {user_id}: {e}")
        conn.close()
        return False


def deactivate_user(user_id: int) -> bool:
    """Deactivate a user (unsubscribe)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE users SET active = 0 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        logger.error(f"Error deactivating user {user_id}: {e}")
        conn.close()
        return False


def get_user_progress(user_id: int) -> Optional[Tuple[int, int]]:
    """
    Get user's current progress.
    Returns (surah, verse) tuple or None if user not found.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT current_surah, current_verse FROM users WHERE user_id = ? AND active = 1",
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        return (result[0], result[1])
    return None


def update_user_progress(user_id: int, surah: int, verse: int) -> bool:
    """Update user's progress to a new verse."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE users
            SET current_surah = ?, current_verse = ?, last_sent_at = ?
            WHERE user_id = ?
            """,
            (surah, verse, datetime.now(), user_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        logger.error(f"Error updating progress for user {user_id}: {e}")
        conn.close()
        return False


def get_active_users() -> List[Tuple[int, int, int, int]]:
    """
    Get all active users with their progress.
    Returns list of (user_id, chat_id, current_surah, current_verse) tuples.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id, chat_id, current_surah, current_verse
        FROM users
        WHERE active = 1
        ORDER BY id
        """
    )
    results = cursor.fetchall()
    conn.close()

    return results


def get_user_stats(user_id: int) -> Optional[dict]:
    """Get detailed stats for a user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT current_surah, current_verse, created_at, last_sent_at, active
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "current_surah": result[0],
            "current_verse": result[1],
            "created_at": result[2],
            "last_sent_at": result[3],
            "active": bool(result[4])
        }
    return None


def should_send_today(user_id: int, timezone_str: str = "America/New_York") -> bool:
    """
    Check if verses should be sent to a user today.
    Returns True if:
    - User has never received verses (last_sent_at is NULL)
    - Last verses were sent on a previous day (not today in EST)

    Args:
        user_id: User ID to check
        timezone_str: Timezone string (default: EST)

    Returns:
        True if verses should be sent today, False otherwise
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT last_sent_at FROM users WHERE user_id = ? AND active = 1",
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            # User not found or inactive
            return False

        last_sent_at = result[0]

        if last_sent_at is None:
            # Never sent verses before
            return True

        # Parse the last_sent_at timestamp
        # SQLite stores it as a string, so we need to parse it
        if isinstance(last_sent_at, str):
            last_sent_dt = datetime.fromisoformat(last_sent_at)
        else:
            last_sent_dt = last_sent_at

        # Get current time in the specified timezone
        tz = pytz.timezone(timezone_str)
        now_tz = datetime.now(tz)

        # Convert last_sent_at to the same timezone
        # Assume it was stored in UTC or naive, localize it
        if last_sent_dt.tzinfo is None:
            # Naive datetime, assume it's in the target timezone
            last_sent_tz = tz.localize(last_sent_dt)
        else:
            last_sent_tz = last_sent_dt.astimezone(tz)

        # Compare dates (not times)
        last_sent_date = last_sent_tz.date()
        today_date = now_tz.date()

        # Send if last_sent_date is before today
        return last_sent_date < today_date

    except Exception as e:
        logger.error(f"Error checking should_send_today for user {user_id}: {e}")
        conn.close()
        return False


def can_request_verses(user_id: int, timezone_str: str = "America/New_York", max_requests: int = 10) -> bool:
    """
    Check if a user can request verses today.
    Returns True if the user has requests remaining today.

    Args:
        user_id: User ID to check
        timezone_str: Timezone string (default: EST)
        max_requests: Maximum requests allowed per day (default: 10)

    Returns:
        True if user can request verses, False otherwise
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT requests_today, last_request_date FROM users WHERE user_id = ? AND active = 1",
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            # User not found or inactive
            return False

        requests_today = result[0] if result[0] is not None else 0
        last_request_date = result[1]

        # Get current date in the specified timezone
        tz = pytz.timezone(timezone_str)
        today_date = datetime.now(tz).date()

        # If last_request_date is None or from a previous day, reset counter
        if last_request_date is None:
            return True

        # Parse last_request_date
        if isinstance(last_request_date, str):
            last_date = datetime.fromisoformat(last_request_date).date()
        else:
            last_date = last_request_date

        # If it's a new day, user can request
        if last_date < today_date:
            return True

        # Check if user has requests remaining today
        return requests_today < max_requests

    except Exception as e:
        logger.error(f"Error checking can_request_verses for user {user_id}: {e}")
        conn.close()
        return False


def increment_request_count(user_id: int, timezone_str: str = "America/New_York") -> bool:
    """
    Increment the request count for a user.
    Resets the counter if it's a new day.

    Args:
        user_id: User ID
        timezone_str: Timezone string (default: EST)

    Returns:
        True if successful, False otherwise
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Get current date in the specified timezone
        tz = pytz.timezone(timezone_str)
        today_date = datetime.now(tz).date()

        cursor.execute(
            "SELECT requests_today, last_request_date FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            return False

        requests_today = result[0] if result[0] is not None else 0
        last_request_date = result[1]

        # Check if it's a new day
        is_new_day = True
        if last_request_date is not None:
            if isinstance(last_request_date, str):
                last_date = datetime.fromisoformat(last_request_date).date()
            else:
                last_date = last_request_date
            is_new_day = last_date < today_date

        # Reset counter if new day, otherwise increment
        new_count = 1 if is_new_day else requests_today + 1

        cursor.execute(
            """
            UPDATE users
            SET requests_today = ?, last_request_date = ?
            WHERE user_id = ?
            """,
            (new_count, today_date.isoformat(), user_id)
        )

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        logger.info(f"Updated request count for user {user_id}: {new_count} requests today")
        return success

    except Exception as e:
        logger.error(f"Error incrementing request count for user {user_id}: {e}")
        conn.close()
        return False


def get_requests_remaining(user_id: int, timezone_str: str = "America/New_York", max_requests: int = 10) -> int:
    """
    Get the number of requests remaining for a user today.

    Args:
        user_id: User ID
        timezone_str: Timezone string (default: EST)
        max_requests: Maximum requests allowed per day (default: 10)

    Returns:
        Number of requests remaining (0-10)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT requests_today, last_request_date FROM users WHERE user_id = ? AND active = 1",
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return 0

        requests_today = result[0] if result[0] is not None else 0
        last_request_date = result[1]

        # Get current date in the specified timezone
        tz = pytz.timezone(timezone_str)
        today_date = datetime.now(tz).date()

        # If last_request_date is None or from a previous day, full quota available
        if last_request_date is None:
            return max_requests

        # Parse last_request_date
        if isinstance(last_request_date, str):
            last_date = datetime.fromisoformat(last_request_date).date()
        else:
            last_date = last_request_date

        # If it's a new day, full quota available
        if last_date < today_date:
            return max_requests

        # Return remaining requests
        return max(0, max_requests - requests_today)

    except Exception as e:
        logger.error(f"Error getting requests_remaining for user {user_id}: {e}")
        conn.close()
        return 0
