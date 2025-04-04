# Automated Backup Solution

This is a comprehensive backup solution built with Python and Docker that demonstrates Linux system administration and DevOps skills.

## Features

- **Directory Backup**: Automatically backs up specified directories
- **Compression**: Creates compressed tar.gz archives of backup data
- **Encryption**: Optional GPG encryption of backup files
- **Retention Policy**: Automatically cleans up old backups based on retention period
- **Notifications**: Email notifications when backups complete or fail
- **Logging**: Comprehensive logging of all operations
- **Containerized**: Runs in Docker for easy deployment
- **Configurable**: Simple configuration file for customization

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/automated-backup-solution.git
cd automated-backup-solution
```

### 2. Edit the configuration file

Edit `backup_config.ini` to specify your backup sources, destinations, and notification settings.

### 3. Run with Docker Compose

```bash
docker-compose up -d
```

## Configuration

The `backup_config.ini` file contains all the configuration settings:

### General Settings

```ini
[General]
backup_root = /backups
log_directory = /logs
retention_days = 30
```

### Source Directories

```ini
[Sources]
source1 = /data/project1
source2 = /data/project2
```

### Encryption Settings

```ini
[Encryption]
enabled = false
gpg_recipient = your_email@example.com
```

### Notification Settings

```ini
[Notification]
enabled = false
smtp_server = smtp.example.com
smtp_port = 587
smtp_user = user@example.com
smtp_password = password
from_email = backup@example.com
to_email = admin@example.com
```

## Running Manually

You can run the backup script manually:

```bash
# Run with default config
python backup.py

# Specify a different config file
python backup.py --config /path/to/config.ini

# Dry run (test without performing backups)
python backup.py --dry-run
```

## Scheduling Backups

### Using Docker

The included Docker Compose file runs the backup daily. You can modify the sleep interval in the entrypoint command.

### Using Cron (without Docker)

Add a cron job to run the backup script on a schedule:

```bash
# Edit crontab
crontab -e

# Add line to run daily at 2am
0 2 * * * /path/to/python /path/to/backup.py --config /path/to/backup_config.ini
```

## Security Considerations

- Store the configuration file securely as it may contain sensitive information
- For production use, store SMTP passwords and encryption keys securely
- Consider using environment variables for sensitive information

## License

MIT License - See LICENSE file for details
