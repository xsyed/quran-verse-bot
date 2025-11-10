# Quran Telegram Bot

A Telegram bot that sends 3 Quran verses daily at 7:00 PM EST to subscribed users. Each user has individual progress tracking, starting from verse 1:1 and progressing sequentially through all 6,236 verses of the Quran.

## Features

- Daily delivery of 3 Quran verses at 7:00 PM EST
- Individual progress tracking for each user
- AI-generated transliteration, translation, and contextual explanations using OpenAI GPT-4o-mini
- Simple subscription management with /start and /stop commands
- Persistent progress storage (resume where you left off)

## Tech Stack

- Python 3.13
- python-telegram-bot (async)
- OpenAI API (gpt-4o-mini)
- SQLite database
- APScheduler
- pytz for timezone management

## Quick Start

You can run this bot either with Docker (recommended) or directly with Python.

### Option A: Docker (Recommended)

#### 1. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Get from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Get from platform.openai.com
OPENAI_API_KEY=your_openai_api_key_here

# Timezone (default: EST)
TIMEZONE=America/New_York

# Send time (7:00 PM EST)
SEND_HOUR=19
SEND_MINUTE=0
```

#### 2. Get Your API Keys

**Telegram Bot Token:**
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the token to your `.env` file

**OpenAI API Key:**
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key to your `.env` file

#### 3. Create Data Directory

```bash
# Create directory for persistent database storage
mkdir -p data
```

#### 4. Run with Docker Compose

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

You should see in the logs:
```
Bot started successfully! Daily verses scheduled for 19:00 America/New_York
```

#### Docker Management Commands

```bash
# View running containers
docker-compose ps

# Restart the bot
docker-compose restart

# Stop the bot
docker-compose stop

# View logs (last 50 lines)
docker-compose logs --tail=50

# Follow logs in real-time
docker-compose logs -f

# Rebuild after code changes
docker-compose up -d --build
```

---

### Option B: Python (Without Docker)

#### 1. Install Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

#### 2. Configure Environment Variables

Follow the same steps as Docker Option A (steps 1-2)

#### 3. Run the Bot

```bash
python main.py
```

You should see:
```
Bot started successfully! Daily verses scheduled for 19:00 America/New_York
```

## Usage

### User Commands

- `/start` - Subscribe to daily verses (begins at Surah 1:1)
- `/stop` - Unsubscribe (progress is saved)

### How It Works

1. User sends `/start` to subscribe
2. Every day at 7:00 PM EST, the bot sends 3 verses
3. Each verse includes:
   - Transliteration in English
   - English translation
   - Context and understanding (100-150 words)
4. Progress automatically advances after each delivery
5. When complete (after 2,079 days), user receives a completion message

## Project Structure

```
quran-telegram-bot/
├── .env                    # API keys (not in git)
├── .env.example            # Template for .env
├── .gitignore              # Git ignore file
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── main.py                 # Bot entry point
├── bot.py                  # Telegram bot handlers
├── database.py             # SQLite database operations
├── openai_service.py       # OpenAI API integration
├── scheduler.py            # Daily verse scheduler
├── quran_data.py           # Quran structure data
└── quran.db                # SQLite database (auto-created)
```

## Database

The bot uses SQLite to track user progress:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    chat_id INTEGER NOT NULL,
    current_surah INTEGER DEFAULT 1,
    current_verse INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sent_at TIMESTAMP
);
```

## Cost Estimation

Using GPT-4o-mini:
- Per verse: ~$0.0001-0.0003
- Per user per day (3 verses): ~$0.0003-0.0009
- 100 users per month: ~$0.90-$2.70
- 1000 users per month: ~$9-$27

## Troubleshooting

**Bot doesn't respond:**
- Check `TELEGRAM_BOT_TOKEN` is correct
- Ensure bot is running: `python main.py`
- Check logs for errors

**OpenAI errors:**
- Verify `OPENAI_API_KEY` is valid
- Check OpenAI account has credits
- Review API rate limits

**Verses not sent at scheduled time:**
- Confirm timezone is correct
- Check system time
- Review scheduler logs

## Database Inspection

```bash
# Open the database
sqlite3 quran.db

# View all users
SELECT * FROM users;

# View active users
SELECT user_id, current_surah, current_verse FROM users WHERE active = 1;

# Reset a user's progress
UPDATE users SET current_surah = 1, current_verse = 1 WHERE user_id = YOUR_USER_ID;
```

## Deployment

### Option 1: Docker on VPS (Recommended)

**Requirements:** VPS with Docker and Docker Compose installed

```bash
# On your VPS
git clone <your-repo-url>
cd quran-telegram-bot

# Configure environment
cp .env.example .env
nano .env  # Add your API keys

# Create data directory
mkdir -p data

# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f
```

**Benefits:**
- Consistent environment across machines
- Easy updates and rollbacks
- Automatic restart on failure
- Isolated from system dependencies

### Option 2: Docker on Local Machine

```bash
# Keep running in background
docker-compose up -d

# Check if running
docker-compose ps
```

### Option 3: Python on VPS (Without Docker)

```bash
# On your VPS
git clone <your-repo-url>
cd quran-telegram-bot

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your API keys

# Run with nohup
nohup python main.py &

# Or use systemd for better management
```

### Option 4: Cloud Platform (Heroku, Railway, etc.)

- Push code to GitHub
- Connect to cloud platform
- Set environment variables in dashboard
- Deploy

## Security

- Never commit `.env` file (already in `.gitignore`)
- Keep API keys secure
- Regularly rotate API keys
- Monitor API usage
- Keep dependencies updated

## License

This is a personal project for learning and daily spiritual reflection. Use responsibly and in accordance with Islamic values.

---

**May Allah accept this effort and make it a source of continuous reward (Sadaqah Jariyah). Ameen.**
