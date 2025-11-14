# Quran Bot Database Backup System

## Overview

This backup system creates timestamped copies of your `quran.db` database file and stores them in a dedicated backup folder outside your project directory.

## Directory Structure

```
/root/
├── quran-verse-bot/          # Your bot project
│   ├── data/
│   │   └── quran.db          # Active database (Docker volume)
│   ├── backup_db.sh          # Backup script
│   └── setup_cron.sh         # Cron setup helper
└── backups/                  # Backup storage (auto-created)
    ├── quran_backup_20250113_020000.db
    ├── quran_backup_20250114_020000.db
    ├── quran_backup_20250115_020000.db
    └── latest.db -> quran_backup_20250115_020000.db
```

## Quick Start

### 1. Make Scripts Executable

```bash
cd /root/quran-verse-bot
chmod +x backup_db.sh setup_cron.sh
```

### 2. Test Manual Backup

```bash
./backup_db.sh
```

You should see output like:
```
[INFO] === Quran Bot Database Backup ===
[INFO] Starting backup process...
[INFO] Backup completed successfully!
[INFO] Backup file: quran_backup_20250113_143022.db
[INFO] Size: 12K
```

### 3. Verify Backup

```bash
ls -lh ../backups/
```

You should see your backup files.

## Automated Backups with Cron

### Option 1: Using the Setup Helper

```bash
./setup_cron.sh
```

This will show you recommended cron schedules and commands.

### Option 2: Manual Cron Setup

**Daily backup at 2:00 AM:**

```bash
crontab -e
```

Add this line:
```
0 2 * * * /root/quran-verse-bot/backup_db.sh >> /root/quran-verse-bot/backup.log 2>&1
```

Save and exit.

### Common Cron Schedules

| Schedule | Description | Cron Expression |
|----------|-------------|-----------------|
| Daily at 2 AM | Recommended | `0 2 * * *` |
| Daily at 4 AM | Alternative | `0 4 * * *` |
| Every 12 hours | Twice daily | `0 */12 * * *` |
| Every 6 hours | Four times daily | `0 */6 * * *` |
| Weekly (Sunday 3 AM) | Once per week | `0 3 * * 0` |

### Verify Cron Job

View your crontab:
```bash
crontab -l
```

Check cron logs:
```bash
# On Ubuntu/Debian
grep CRON /var/log/syslog

# Check backup script logs
tail -f /root/quran-verse-bot/backup.log
```

## Backup Configuration

You can customize the backup behavior by editing `backup_db.sh`:

### Keep Only Last 30 Backups

```bash
MAX_BACKUPS=30  # Change this number or set to 0 for unlimited
```

### Change Backup Location

```bash
BACKUP_DIR="/path/to/your/custom/backup/location"
```

## Restoring from Backup

### 1. Stop the Bot

```bash
cd /root/quran-verse-bot
docker-compose down
```

### 2. Restore Database

```bash
# Copy backup to active database location
cp ../backups/quran_backup_YYYYMMDD_HHMMSS.db ./data/quran.db

# Or restore latest backup
cp ../backups/latest.db ./data/quran.db
```

### 3. Restart the Bot

```bash
docker-compose up -d
```

## Monitoring Backups

### Check Backup Status

```bash
# List all backups
ls -lht ../backups/

# Count backups
ls -1 ../backups/quran_backup_*.db | wc -l

# Check total backup size
du -sh ../backups/

# View latest backup info
ls -lh ../backups/latest.db
```

### Check Last Backup Time

```bash
stat ../backups/latest.db
```

## Backup to Remote Location

### Using rsync (Recommended)

```bash
# Add to your backup script or create separate script
rsync -avz /root/backups/ user@remote-server:/path/to/remote/backups/
```

### Using scp

```bash
scp /root/backups/latest.db user@remote-server:/path/to/remote/backups/
```

### Using Cloud Storage (example with rclone)

```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure cloud provider
rclone config

# Sync backups
rclone sync /root/backups remote:quran-bot-backups
```

## Troubleshooting

### Backup Script Fails

**Check database exists:**
```bash
ls -lh /root/quran-verse-bot/data/quran.db
```

**Check permissions:**
```bash
ls -ld /root/backups
chmod 755 /root/backups
```

**Run backup manually with verbose output:**
```bash
bash -x ./backup_db.sh
```

### Cron Job Not Running

**Check cron service:**
```bash
sudo systemctl status cron
```

**Check cron logs:**
```bash
tail -f /var/log/syslog | grep CRON
```

**Verify crontab:**
```bash
crontab -l
```

**Test cron environment:**
```bash
# Add this temporary cron job to verify cron is working
* * * * * echo "Cron is working - $(date)" >> /tmp/cron_test.log
```

## Best Practices

1. **Test Backups Regularly**: Periodically test restoring from backup
2. **Monitor Disk Space**: Ensure you have enough space for backups
3. **Off-site Backups**: Consider syncing to remote location or cloud
4. **Verify Backups**: Occasionally check that backup files are valid
5. **Document Restore Process**: Keep these instructions accessible

## Security Notes

- Backup files contain user data - protect them appropriately
- Set proper file permissions on backup directory
- Consider encrypting backups if storing remotely
- Keep backup location secure and access-controlled

## Support

If you encounter issues:
1. Check backup.log for error messages
2. Verify Docker volume is properly mounted
3. Ensure sufficient disk space
4. Check file permissions
5. Test manual backup before setting up cron

---

**May your backups be successful and your data always safe!**
