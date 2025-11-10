#!/bin/sh
# Health check script for Quran Telegram Bot
# Verifies that the Python process is running

# Check if the main.py process is running
if pgrep -f "python main.py" > /dev/null 2>&1; then
    exit 0  # Healthy
else
    exit 1  # Unhealthy
fi
