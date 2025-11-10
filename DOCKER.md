# Docker Setup Guide for Quran Telegram Bot

## Quick Start

### Prerequisites

- Docker installed on your system
- Docker Compose installed (usually comes with Docker Desktop)

### Setup Steps

1. **Clone or navigate to the project directory**
   ```bash
   cd quran-telegram-bot
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` and add your API keys**
   ```bash
   nano .env  # or use your preferred editor
   ```

   Required variables:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
   OPENAI_API_KEY=your_openai_api_key
   TIMEZONE=America/New_York
   SEND_HOUR=19
   SEND_MINUTE=0
   ```

4. **Create data directory for persistent database**
   ```bash
   mkdir -p data
   ```

5. **Start the bot**
   ```bash
   docker-compose up -d
   ```

6. **Check logs to verify it's running**
   ```bash
   docker-compose logs -f
   ```

   You should see:
   ```
   Bot started successfully! Daily verses scheduled for 19:00 America/New_York
   ```

7. **Check container health status**
   ```bash
   docker-compose ps
   ```

   You should see `(healthy)` in the status column after ~40 seconds.

## Restart Policy & Health Checks

### Restart Policy

The bot uses an intelligent restart policy that prevents infinite restart loops:

**Configuration:**
- **Condition**: `on-failure` - Only restarts if the container exits with an error
- **Max Attempts**: `5` - Stops trying after 5 failed restart attempts
- **Delay**: `10s` - Waits 10 seconds between each restart attempt
- **Window**: `120s` - If the container runs for 2+ minutes, the restart counter resets

**What this means:**
- ✅ Automatically recovers from temporary failures (network issues, API hiccups)
- ✅ Prevents infinite restart loops from configuration errors (bad API keys)
- ✅ Saves resources by giving up after 5 attempts
- ✅ Resets counter if bot runs successfully for 2 minutes

**Example scenario:**
1. Bot crashes due to temporary network issue → Waits 10s → Restarts (Attempt 1)
2. Still failing → Waits 10s → Restarts (Attempt 2)
3. Still failing → Waits 10s → Restarts (Attempt 3)
4. Still failing → Waits 10s → Restarts (Attempt 4)
5. Still failing → Waits 10s → Restarts (Attempt 5)
6. Still failing → **Stops and stays stopped** (prevents resource waste)

To restart manually after max attempts reached:
```bash
docker-compose restart
# or
docker-compose up -d
```

### Health Checks

The container includes automatic health monitoring:

**Configuration:**
- **Test**: Checks if Python process is running
- **Interval**: Every 30 seconds
- **Timeout**: 10 seconds max wait for response
- **Retries**: 3 consecutive failures before marking unhealthy
- **Start Period**: 40 second grace period for initial startup

**Health States:**
- `starting` - Initial 40 seconds after container starts
- `healthy` - Bot process is running normally
- `unhealthy` - Process not running (after 3 failed checks)

**Check health status:**
```bash
# Quick check
docker-compose ps

# Detailed health info
docker inspect quran-telegram-bot --format='{{.State.Health.Status}}'

# Full health check history
docker inspect quran-telegram-bot --format='{{json .State.Health}}' | jq
```

**What triggers unhealthy status:**
- Python process crashed and didn't restart
- Process is stuck/frozen
- Container is running but bot is not

**Note:** An unhealthy status does NOT automatically restart the container. It only provides visibility. The restart policy handles actual restarts based on exit codes.

## Docker Commands

### Basic Operations

```bash
# Start the bot (detached mode)
docker-compose up -d

# Stop the bot
docker-compose down

# Restart the bot
docker-compose restart

# Stop without removing container
docker-compose stop

# Start existing container
docker-compose start
```

### Monitoring & Logs

```bash
# View logs (real-time)
docker-compose logs -f

# View last 50 lines of logs
docker-compose logs --tail=50

# Check if container is running
docker-compose ps

# Check container status with health
docker ps | grep quran-telegram-bot

# Check detailed health status
docker inspect quran-telegram-bot --format='{{.State.Health.Status}}'

# View health check logs
docker inspect quran-telegram-bot --format='{{json .State.Health}}' | jq
```

### Updates & Maintenance

```bash
# Rebuild after code changes
docker-compose up -d --build

# Pull latest base image and rebuild
docker-compose build --no-cache
docker-compose up -d

# View resource usage
docker stats quran-telegram-bot
```

### Database Management

```bash
# Access SQLite database
docker-compose exec quran-bot sqlite3 /app/data/quran.db

# In SQLite shell:
sqlite> SELECT * FROM users;
sqlite> .exit

# Backup database
cp data/quran.db data/quran.db.backup

# Restore database
cp data/quran.db.backup data/quran.db
docker-compose restart
```

### Troubleshooting

```bash
# View detailed container info
docker inspect quran-telegram-bot

# Enter container shell for debugging
docker-compose exec quran-bot /bin/bash

# View all Docker volumes
docker volume ls

# Remove everything and start fresh
docker-compose down
rm -rf data/quran.db
docker-compose up -d
```

## File Structure

```
quran-telegram-bot/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore          # Files to exclude from image
├── .env                   # Environment variables (not in git)
├── .env.example           # Environment template
├── data/                  # Persistent database directory (mounted volume)
│   └── quran.db          # SQLite database (auto-created)
└── [Python files...]
```

## Volume Mounting

The `data` directory is mounted as a Docker volume to ensure database persistence:

```yaml
volumes:
  - ./data:/app/data
```

This means:
- Database survives container restarts
- Database survives container deletions
- You can backup `data/quran.db` directly from your host machine

## Environment Variables

Environment variables are loaded from `.env` file via docker-compose:

```yaml
env_file:
  - .env
```

The container also sets:
- `TZ=America/New_York` - Ensures correct timezone for scheduling
- `PYTHONUNBUFFERED=1` - Ensures logs appear immediately

## Networking

The bot doesn't expose any ports since it only makes outgoing connections to:
- Telegram API
- OpenAI API

## Resource Limits (Optional)

To limit container resources, add to `docker-compose.yml`:

```yaml
services:
  quran-bot:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          memory: 256M
```

## Production Deployment

### VPS Deployment

1. **SSH into your VPS**
   ```bash
   ssh user@your-vps-ip
   ```

2. **Install Docker**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose
   sudo systemctl enable docker
   sudo systemctl start docker

   # Add user to docker group
   sudo usermod -aG docker $USER
   # Log out and back in for group changes
   ```

3. **Clone repository**
   ```bash
   git clone https://github.com/your-username/quran-telegram-bot.git
   cd quran-telegram-bot
   ```

4. **Configure and start**
   ```bash
   cp .env.example .env
   nano .env  # Add your API keys
   mkdir -p data
   docker-compose up -d
   ```

5. **Enable auto-start on boot**

   Docker Compose with `restart: unless-stopped` will automatically:
   - Start on system boot
   - Restart if it crashes
   - Stay stopped only if you explicitly stop it

6. **Monitor**
   ```bash
   docker-compose logs -f
   ```

### Using Docker Hub (Optional)

```bash
# Build and tag
docker build -t yourusername/quran-telegram-bot:latest .

# Push to Docker Hub
docker push yourusername/quran-telegram-bot:latest

# On production server, modify docker-compose.yml:
services:
  quran-bot:
    image: yourusername/quran-telegram-bot:latest
    # ... rest of config
```

## Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Set proper file permissions**
   ```bash
   chmod 600 .env
   chmod 700 data
   ```
3. **Regularly update base image**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```
4. **Monitor logs for unauthorized access attempts**
5. **Keep API keys secure and rotate regularly**

## Benefits of Docker

- **Consistency**: Same environment everywhere (dev, staging, prod)
- **Isolation**: Bot runs in its own container
- **Easy deployment**: One command to start/stop
- **Portability**: Works on any system with Docker
- **Rollback**: Easy to revert to previous versions
- **Resource control**: Limit CPU/memory usage
- **Auto-restart**: Automatically recovers from crashes

## Common Issues

### Container exits immediately

```bash
# Check logs for errors
docker-compose logs

# Common causes:
# - Missing .env file
# - Invalid API keys
# - Syntax errors in code
```

### Container keeps restarting

```bash
# Check how many times it has restarted
docker-compose ps
docker inspect quran-telegram-bot --format='{{.RestartCount}}'

# View logs to identify the error
docker-compose logs --tail=100

# Common causes and solutions:
# 1. Invalid TELEGRAM_BOT_TOKEN → Check .env file
# 2. Invalid OPENAI_API_KEY → Verify API key is correct
# 3. Network issues → Check internet connectivity
# 4. Python code errors → Review logs for stack traces
```

**Note:** The container will stop after 5 failed restart attempts. To retry:
```bash
# Fix the underlying issue in .env or code, then:
docker-compose restart
```

### Container stuck in "unhealthy" status

```bash
# Check health check logs
docker inspect quran-telegram-bot --format='{{json .State.Health}}' | jq

# View what the health check is seeing
docker-compose exec quran-bot /app/healthcheck.sh
echo $?  # 0 = healthy, 1 = unhealthy

# Manually check if process is running
docker-compose exec quran-bot ps aux | grep python

# Common causes:
# - Bot process crashed but container is still running
# - Process is frozen/stuck

# Solution: Restart the container
docker-compose restart
```

### Max restart attempts reached

If you see the container stopped after multiple restart attempts:

```bash
# 1. Check logs to identify the root cause
docker-compose logs --tail=200

# 2. Fix the issue (e.g., update .env with correct API keys)

# 3. Restart the container
docker-compose restart

# 4. Monitor to ensure it stays up
docker-compose logs -f
```

### Database permission errors

```bash
# Fix permissions
chmod -R 755 data
docker-compose restart
```

### Timezone issues

```bash
# Verify timezone in container
docker-compose exec quran-bot date

# Should show America/New_York time
```

### Can't connect to Telegram/OpenAI

```bash
# Check internet connectivity
docker-compose exec quran-bot ping -c 3 api.telegram.org

# Check firewall rules
# Ensure outbound HTTPS (443) is allowed
```

## Support

For issues specific to Docker setup:
1. Check logs: `docker-compose logs`
2. Verify `.env` file is configured correctly
3. Ensure data directory exists and has proper permissions
4. Check Docker daemon is running: `docker ps`

---

**May this bot serve as a tool for continuous learning and spiritual growth. Ameen.**
