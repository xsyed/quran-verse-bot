import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import bot


class TestResetLimitCommand(unittest.IsolatedAsyncioTestCase):
    async def test_resetlimit_success_for_active_user(self):
        update = SimpleNamespace(
            effective_user=SimpleNamespace(id=123),
            message=SimpleNamespace(reply_text=AsyncMock()),
        )
        context = SimpleNamespace()

        with patch("bot.database.get_user_progress", return_value=(1, 1)), \
             patch("bot.database.reset_request_count", return_value=True) as mock_reset, \
             patch("bot.os.getenv", return_value="America/New_York"):
            await bot.resetlimit_command(update, context)

        mock_reset.assert_called_once_with(123, "America/New_York")
        update.message.reply_text.assert_awaited_once()
        sent_message = update.message.reply_text.await_args.args[0]
        self.assertIn("reset to 0", sent_message)
        self.assertIn("/anotherone", sent_message)

    async def test_resetlimit_requires_active_subscription(self):
        update = SimpleNamespace(
            effective_user=SimpleNamespace(id=123),
            message=SimpleNamespace(reply_text=AsyncMock()),
        )
        context = SimpleNamespace()

        with patch("bot.database.get_user_progress", return_value=None), \
             patch("bot.database.reset_request_count") as mock_reset:
            await bot.resetlimit_command(update, context)

        mock_reset.assert_not_called()
        update.message.reply_text.assert_awaited_once()
        sent_message = update.message.reply_text.await_args.args[0]
        self.assertIn("Please use /start", sent_message)

    async def test_resetlimit_db_failure_returns_error_message(self):
        update = SimpleNamespace(
            effective_user=SimpleNamespace(id=123),
            message=SimpleNamespace(reply_text=AsyncMock()),
        )
        context = SimpleNamespace()

        with patch("bot.database.get_user_progress", return_value=(1, 1)), \
             patch("bot.database.reset_request_count", return_value=False):
            await bot.resetlimit_command(update, context)

        update.message.reply_text.assert_awaited_once()
        sent_message = update.message.reply_text.await_args.args[0]
        self.assertIn("error resetting your limit", sent_message)


if __name__ == "__main__":
    unittest.main()
