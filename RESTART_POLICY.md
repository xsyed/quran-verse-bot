# Restart Policy & Health Check Implementation

## Overview

This document explains the restart policy and health check implementation for the Quran Telegram Bot Docker container.

## Problem Solved

**Before**: Using `restart: unless-stopped` caused infinite restart loops when the bot had persistent errors (e.g., invalid API keys), wasting resources and filling logs.

**After**: Intelligent restart policy with health monitoring that:
- Recovers from temporary failures
- Stops after persistent failures
- Monitors container health
- Prevents resource waste

## Implementation Details

### 1. Restart Policy

**Configuration** (`docker-compose.yml`):
```yaml
deploy:
  restart_policy:
    condition: on-failure      # Only restart on errors, not manual stops
    delay: 10s                  # Wait 10 seconds between attempts
    max_attempts: 5             # Stop after 5 failed attempts
    window: 120s                # Reset counter if runs for 2+ minutes
```

**Behavior**:

| Scenario | Result |
|----------|--------|
| Temporary network issue | Restarts up to 5 times with 10s delays |
| Invalid API key | Stops after 5 attempts (prevents infinite loop) |
| Bot runs for 2+ minutes | Restart counter resets to 0 |
| Manual stop (`docker-compose down`) | Does NOT auto-restart |
| Container crash | Auto-restarts (up to 5 times) |

**Example Timeline**:
```
00:00:00 - Bot starts
00:00:05 - Crashes (bad config)
00:00:15 - Restart attempt 1 (after 10s delay)
00:00:20 - Crashes again
00:00:30 - Restart attempt 2 (after 10s delay)
00:00:35 - Crashes again
00:00:45 - Restart attempt 3 (after 10s delay)
00:00:50 - Crashes again
00:01:00 - Restart attempt 4 (after 10s delay)
00:01:05 - Crashes again
00:01:15 - Restart attempt 5 (after 10s delay)
00:01:20 - Crashes again
00:01:30 - STOPPED (max attempts reached)
```

### 2. Health Check

**Configuration** (`docker-compose.yml`):
```yaml
healthcheck:
  test: ["CMD-SHELL", "/app/healthcheck.sh"]
  interval: 30s        # Check every 30 seconds
  timeout: 10s         # Wait up to 10 seconds for response
  retries: 3           # 3 consecutive failures = unhealthy
  start_period: 40s    # Grace period during startup
```

**Health Check Script** (`healthcheck.sh`):
```bash
#!/bin/sh
# Verifies that the Python process is running

if pgrep -f "python main.py" > /dev/null 2>&1; then
    exit 0  # Healthy
else
    exit 1  # Unhealthy
fi
```

**Health States**:

1. **starting** (0-40 seconds)
   - Grace period for bot initialization
   - Failed checks don't count against health
   - Normal for startup phase

2. **healthy**
   - Python process is running
   - Health check passes
   - Everything working normally

3. **unhealthy**
   - Health check failed 3 times in a row
   - Python process not detected
   - Container may still be running

**Important**: Health check status does NOT trigger restarts. It only provides visibility. The restart policy handles restarts based on exit codes.

### 3. Files Modified

1. **`docker-compose.yml`**
   - Removed `restart: unless-stopped`
   - Added `deploy.restart_policy` configuration
   - Added `healthcheck` configuration

2. **`Dockerfile`**
   - Added `procps` package (provides `pgrep` command)
   - Added `healthcheck.sh` script
   - Made script executable

3. **`healthcheck.sh`** (new file)
   - Simple shell script
   - Checks if Python process is running
   - Returns 0 (healthy) or 1 (unhealthy)

4. **`DOCKER.md`**
   - Added "Restart Policy & Health Checks" section
   - Added health check monitoring commands
   - Added troubleshooting for restart issues

## Usage

### Check Container Status

```bash
# Quick status check
docker-compose ps

# Output example:
NAME                   STATUS                    HEALTH
quran-telegram-bot     Up 5 minutes              healthy
```

### View Health Check Details

```bash
# Get current health status
docker inspect quran-telegram-bot --format='{{.State.Health.Status}}'

# View full health check history (requires jq)
docker inspect quran-telegram-bot --format='{{json .State.Health}}' | jq

# Output example:
{
  "Status": "healthy",
  "FailingStreak": 0,
  "Log": [
    {
      "Start": "2025-11-09T19:00:00.000Z",
      "End": "2025-11-09T19:00:00.100Z",
      "ExitCode": 0,
      "Output": ""
    }
  ]
}
```

### Check Restart Count

```bash
# See how many times container has restarted
docker inspect quran-telegram-bot --format='{{.RestartCount}}'
```

### Manual Restart After Max Attempts

If the container stops after reaching max restart attempts:

```bash
# Fix the underlying issue (e.g., update .env with correct API keys)
nano .env

# Then restart
docker-compose restart

# Or rebuild and restart
docker-compose up -d --build
```

## Troubleshooting Scenarios

### Scenario 1: Container Keeps Restarting

**Symptoms**:
- Container restarts repeatedly
- Logs show errors
- Restart count increasing

**Solution**:
```bash
# Check logs to identify the error
docker-compose logs --tail=100

# Common issues:
# - Invalid TELEGRAM_BOT_TOKEN
# - Invalid OPENAI_API_KEY
# - Network connectivity issues

# Fix the issue in .env
nano .env

# Restart
docker-compose restart
```

### Scenario 2: Container Stopped After 5 Attempts

**Symptoms**:
- Container shows as "Exited"
- Restart count is 5
- Container won't auto-restart

**Solution**:
```bash
# View logs to see what failed
docker-compose logs --tail=200

# Fix the root cause (usually .env configuration)
nano .env

# Manually restart
docker-compose restart

# Monitor to ensure it stays up
docker-compose logs -f
```

### Scenario 3: Container Shows "unhealthy"

**Symptoms**:
- `docker-compose ps` shows "unhealthy"
- Container is running but health check fails

**Solution**:
```bash
# Check what the health check sees
docker-compose exec quran-bot /app/healthcheck.sh
echo $?  # Should be 0 if healthy

# Manually verify process is running
docker-compose exec quran-bot ps aux | grep python

# If process is not running, restart
docker-compose restart
```

### Scenario 4: Bot Working But Shows "starting"

**Symptoms**:
- Bot is functioning
- Status shows "starting" for extended period

**Explanation**: This is normal during the first 40 seconds. If it persists beyond that, the health check might be failing.

**Solution**:
```bash
# Wait 40 seconds from container start
# If still showing "starting":

# Check health check logs
docker inspect quran-telegram-bot --format='{{json .State.Health}}' | jq

# Verify pgrep command works
docker-compose exec quran-bot which pgrep
docker-compose exec quran-bot pgrep -f "python main.py"
```

## Benefits

### 1. Prevents Infinite Restart Loops
- **Before**: Container would restart forever with bad config
- **After**: Stops after 5 attempts, saving resources

### 2. Automatic Recovery from Transient Issues
- **Before**: Manual restart required for temporary network issues
- **After**: Auto-recovers from temporary failures

### 3. Resource Conservation
- **Before**: Wasted CPU/logs during restart loops
- **After**: 10s delay between restarts, stops after 5 attempts

### 4. Better Visibility
- **Before**: No easy way to know if bot process is healthy
- **After**: Health status visible in `docker-compose ps`

### 5. Smart Retry Logic
- **Before**: No concept of "success window"
- **After**: Restart counter resets after 2 minutes of uptime

## Configuration Tuning

You can adjust these values in `docker-compose.yml`:

```yaml
deploy:
  restart_policy:
    delay: 10s          # Change to 5s for faster retries
    max_attempts: 5     # Change to 10 for more retry attempts
    window: 120s        # Change to 60s for faster counter reset

healthcheck:
  interval: 30s        # Change to 60s for less frequent checks
  retries: 3           # Change to 5 for more tolerance
  start_period: 40s    # Change to 60s if bot takes longer to start
```

**Recommendations**:
- Keep `delay` at 10s or higher to avoid rapid restart loops
- Set `max_attempts` between 3-10 depending on your tolerance
- Set `window` to 2-5 minutes for reasonable success threshold
- Keep `interval` at 30-60s for balanced monitoring

## Testing

To test the restart policy:

```bash
# 1. Start the bot normally
docker-compose up -d

# 2. Simulate a crash by stopping the process inside container
docker-compose exec quran-bot pkill -f "python main.py"

# 3. Watch it restart automatically
docker-compose logs -f

# 4. To test max attempts, keep killing it 5 times
# After 5th kill, it should stop and not restart
```

To test health checks:

```bash
# 1. Start the bot
docker-compose up -d

# 2. Wait 40 seconds (start period)
sleep 40

# 3. Check health
docker-compose ps  # Should show "healthy"

# 4. Kill the process
docker-compose exec quran-bot pkill -f "python main.py"

# 5. Wait 90+ seconds (3 failed checks at 30s interval)
sleep 100

# 6. Check health again
docker-compose ps  # Should show "unhealthy"
```

## Monitoring in Production

For production deployments, consider:

1. **Log Aggregation**
   - Send logs to centralized logging (e.g., ELK stack)
   - Set up alerts on restart events

2. **Health Check Monitoring**
   - Monitor health status externally
   - Alert when status is "unhealthy" for extended period

3. **Restart Alerts**
   - Alert when restart count > 0
   - Alert when container stops (max attempts reached)

4. **Metrics Collection**
   - Track uptime percentage
   - Monitor restart frequency
   - Track health check pass/fail rate

Example monitoring command:
```bash
# Continuous monitoring script
while true; do
  echo "=== $(date) ==="
  echo "Status: $(docker inspect quran-telegram-bot --format='{{.State.Status}}')"
  echo "Health: $(docker inspect quran-telegram-bot --format='{{.State.Health.Status}}')"
  echo "Restarts: $(docker inspect quran-telegram-bot --format='{{.RestartCount}}')"
  echo ""
  sleep 60
done
```

## Summary

The implementation provides:
- ✅ Intelligent restart policy with limits
- ✅ Automatic recovery from temporary failures
- ✅ Prevention of infinite restart loops
- ✅ Container health monitoring
- ✅ Resource-efficient operation
- ✅ Better operational visibility

This ensures the bot is reliable, self-healing, and doesn't waste resources on persistent configuration errors.
