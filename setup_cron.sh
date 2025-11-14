#!/bin/bash

###############################################################################
# Cron Job Setup Script for Quran Bot Database Backups
# Description: Helps you set up automated daily backups using cron
# Usage: ./setup_cron.sh
###############################################################################

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_db.sh"

echo -e "${GREEN}=== Quran Bot Backup Cron Setup ===${NC}"
echo ""
echo "This script will help you set up automated daily backups."
echo ""

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${YELLOW}Error: backup_db.sh not found at $BACKUP_SCRIPT${NC}"
    exit 1
fi

# Make backup script executable
chmod +x "$BACKUP_SCRIPT"
echo -e "${GREEN}✓${NC} Made backup_db.sh executable"

echo ""
echo "Suggested cron schedule options:"
echo ""
echo "1. Daily at 2:00 AM:  0 2 * * *"
echo "2. Daily at 4:00 AM:  0 4 * * *"
echo "3. Every 12 hours:    0 */12 * * *"
echo "4. Every 6 hours:     0 */6 * * *"
echo ""

# Default cron job (daily at 2 AM)
CRON_SCHEDULE="0 2 * * *"
CRON_JOB="$CRON_SCHEDULE $BACKUP_SCRIPT >> $SCRIPT_DIR/backup.log 2>&1"

echo "Recommended cron job:"
echo "$CRON_JOB"
echo ""
echo "To add this to your crontab, run:"
echo ""
echo -e "${YELLOW}crontab -e${NC}"
echo ""
echo "Then add this line:"
echo -e "${GREEN}$CRON_JOB${NC}"
echo ""
echo "Or run this command to add it automatically:"
echo ""
echo -e "${YELLOW}(crontab -l 2>/dev/null; echo \"$CRON_JOB\") | crontab -${NC}"
echo ""
echo "To view your current crontab:"
echo -e "${YELLOW}crontab -l${NC}"
echo ""
