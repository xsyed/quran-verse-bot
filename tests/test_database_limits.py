import os
import sqlite3
import tempfile
import unittest
from datetime import datetime

import pytz

import database


class TestDatabaseResetLimit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_name = database.DB_NAME
        database.DB_NAME = os.path.join(self.temp_dir.name, "test_quran.db")

        database.init_db()
        database.add_user(1001, 2001)

    def tearDown(self):
        database.DB_NAME = self.original_db_name
        self.temp_dir.cleanup()

    def _set_requests(self, requests_today: int, request_date: str):
        conn = sqlite3.connect(database.DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET requests_today = ?, last_request_date = ? WHERE user_id = ?",
            (requests_today, request_date, 1001),
        )
        conn.commit()
        conn.close()

    def _get_requests_row(self):
        conn = sqlite3.connect(database.DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT requests_today, last_request_date FROM users WHERE user_id = ?",
            (1001,),
        )
        row = cursor.fetchone()
        conn.close()
        return row

    def test_reset_active_user_sets_zero_for_today(self):
        timezone_str = "America/New_York"
        today = datetime.now(pytz.timezone(timezone_str)).date().isoformat()
        self._set_requests(20, today)

        success = database.reset_request_count(1001, timezone_str)

        self.assertTrue(success)
        requests_today, last_request_date = self._get_requests_row()
        self.assertEqual(requests_today, 0)
        self.assertEqual(last_request_date, today)

    def test_reset_inactive_user_returns_false_and_does_not_change_row(self):
        timezone_str = "America/New_York"
        today = datetime.now(pytz.timezone(timezone_str)).date().isoformat()
        self._set_requests(12, today)
        database.deactivate_user(1001)

        success = database.reset_request_count(1001, timezone_str)

        self.assertFalse(success)
        requests_today, last_request_date = self._get_requests_row()
        self.assertEqual(requests_today, 12)
        self.assertEqual(last_request_date, today)

    def test_can_request_verses_is_true_after_reset(self):
        timezone_str = "America/New_York"
        today = datetime.now(pytz.timezone(timezone_str)).date().isoformat()
        self._set_requests(20, today)

        database.reset_request_count(1001, timezone_str)

        self.assertTrue(database.can_request_verses(1001, timezone_str))

    def test_increment_after_reset_starts_at_one(self):
        timezone_str = "America/New_York"
        today = datetime.now(pytz.timezone(timezone_str)).date().isoformat()
        self._set_requests(20, today)

        reset_success = database.reset_request_count(1001, timezone_str)
        increment_success = database.increment_request_count(1001, timezone_str)

        self.assertTrue(reset_success)
        self.assertTrue(increment_success)
        requests_today, last_request_date = self._get_requests_row()
        self.assertEqual(requests_today, 1)
        self.assertEqual(last_request_date, today)


if __name__ == "__main__":
    unittest.main()
