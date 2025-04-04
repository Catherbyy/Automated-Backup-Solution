#!/usr/bin/env python3
"""
Automated Backup Solution
-------------------------
This script performs automated backups of specified directories,
with compression, optional encryption, logging, and notifications.
"""

import os
import sys
import time
import argparse
import logging
import tarfile
import shutil
import smtplib
import configparser
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path


class BackupManager:
    """Manages the backup process including compression, encryption, and notifications."""
    
    def __init__(self, config_file="backup_config.ini"):
        """Initialize with configuration file path."""
        self.config = configparser.ConfigParser()
        config_path = Path(config_file)
        
        if not config_path.exists():
            self.create_default_config(config_path)
        
        self.config.read(config_path)
        
        # Configure logging
        log_dir = Path(self.config.get('General', 'log_directory', fallback='logs'))
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'backup.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('backup_manager')
        self.logger.info("Backup Manager initialized")
    
    def create_default_config(self, config_path):
        """Create a default configuration file if none exists."""
        self.config['General'] = {
            'backup_root': '/backups',
            'log_directory': 'logs',
            'retention_days': '30'
        }
        
        self.config['Sources'] = {
            'source1': '/path/to/dir1',
            'source2': '/path/to/dir2'
        }
        
        self.config['Encryption'] = {
            'enabled': 'false',
            'gpg_recipient': 'your_email@example.com'
        }
        
        self.config['Notification'] = {
            'enabled': 'false',
            'smtp_server': 'smtp.example.com',
            'smtp_port': '587',
            'smtp_user': 'user@example.com',
            'smtp_password': 'password',
            'from_email': 'backup@example.com',
            'to_email': 'admin@example.com'
        }
        
        with open(config_path, 'w') as f:
            self.config.write(f)
        
        print(f"Default configuration created at {config_path}")
        print("Please edit the configuration file with your settings before running a backup.")
        sys.exit(0)
    
    def run_backup(self):
        """Run the complete backup process."""
        start_time = time.time()
        self.logger.info("Starting backup process")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root = Path(self.config.get('General', 'backup_root'))
        backup_root.mkdir(exist_ok=True, parents=True)
        
        backup_dir = backup_root / timestamp
        backup_dir.mkdir(exist_ok=True)
        
        successful_backups = []
        failed_backups = []
        
        # Process each source directory
        for source_name, source_path in self.config.items('Sources'):
            source_path = Path(source_path)
            if not source_path.exists():
                self.logger.error(f"Source path '{source_path}' does not exist. Skipping.")
                failed_backups.append((source_name, str(source_path), "Source path does not exist"))
                continue
            
            try:
                archive_path = self._create_archive(source_name, source_path, backup_dir, timestamp)
                
                if self.config.getboolean('Encryption', 'enabled', fallback=False):
                    archive_path = self._encrypt_archive(archive_path)
                
                successful_backups.append((source_name, str(source_path), str(archive_path)))
                self.logger.info(f"Successfully backed up {source_name} to {archive_path}")
            
            except Exception as e:
                self.logger.error(f"Failed to backup {source_name}: {str(e)}")
                failed_backups.append((source_name, str(source_path), str(e)))
        
        # Clean up old backups
        self._cleanup_old_backups()
        
        # Send notification if enabled
        if self.config.getboolean('Notification', 'enabled', fallback=False):
            self._send_notification(successful_backups, failed_backups, time.time() - start_time)
        
        self.logger.info(f"Backup process completed in {time.time() - start_time:.2f} seconds")
        return successful_backups, failed_backups
    
    def _create_archive(self, source_name, source_path, backup_dir, timestamp):
        """Create a compressed archive of the source directory."""
        self.logger.info(f"Creating archive for {source_name} from {source_path}")
        
        archive_name = f"{source_name}_{timestamp}.tar.gz"
        archive_path = backup_dir / archive_name
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(source_path, arcname=source_path.name)
        
        self.logger.info(f"Archive created at {archive_path}")
        return archive_path
    
    def _encrypt_archive(self, archive_path):
        """Encrypt the archive using GPG."""
        recipient = self.config.get('Encryption', 'gpg_recipient')
        self.logger.info(f"Encrypting archive {archive_path} for recipient {recipient}")
        
        encrypted_path = Path(f"{archive_path}.gpg")
        cmd = ["gpg", "--recipient", recipient, "--output", str(encrypted_path), "--encrypt", str(archive_path)]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            self.logger.info(f"Encryption successful: {encrypted_path}")
            
            # Remove the unencrypted archive
            archive_path.unlink()
            return encrypted_path
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Encryption failed: {e.stderr.decode()}")
            raise
    
    def _cleanup_old_backups(self):
        """Remove backups older than the retention period."""
        retention_days = int(self.config.get('General', 'retention_days', fallback='30'))
        backup_root = Path(self.config.get('General', 'backup_root'))
        
        self.logger.info(f"Cleaning up backups older than {retention_days} days")
        
        cutoff_time = time.time() - (retention_days * 86400)
        
        for item in backup_root.iterdir():
            if item.is_dir() and item.stat().st_mtime < cutoff_time:
                self.logger.info(f"Removing old backup directory: {item}")
                shutil.rmtree(item)
    
    def _send_notification(self, successful_backups, failed_backups, elapsed_time):
        """Send email notification about the backup status."""
        self.logger.info("Sending backup notification email")
        
        smtp_server = self.config.get('Notification', 'smtp_server')
        smtp_port = self.config.getint('Notification', 'smtp_port')
        smtp_user = self.config.get('Notification', 'smtp_user')
        smtp_password = self.config.get('Notification', 'smtp_password')
        from_email = self.config.get('Notification', 'from_email')
        to_email = self.config.get('Notification', 'to_email')
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        
        # Determine subject based on success/failure
        if failed_backups:
            msg['Subject'] = f"[ALERT] Backup job completed with {len(failed_backups)} failures"
        else:
            msg['Subject'] = f"Backup job completed successfully - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Build email body
        body = f"""
        Backup Job Report
        ----------------
        Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Elapsed Time: {elapsed_time:.2f} seconds
        
        Summary:
        - Successful Backups: {len(successful_backups)}
        - Failed Backups: {len(failed_backups)}
        
        """
        
        if successful_backups:
            body += "\nSuccessful Backups:\n"
            for name, source, dest in successful_backups:
                body += f"- {name}: {source} → {dest}\n"
        
        if failed_backups:
            body += "\nFailed Backups:\n"
            for name, source, error in failed_backups:
                body += f"- {name}: {source} - Error: {error}\n"
        
        body += "\n\nThis is an automated message. Please do not reply."
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            self.logger.info("Notification email sent successfully")
        
        except Exception as e:
            self.logger.error(f"Failed to send notification email: {str(e)}")


def main():
    """Main function to run the backup process."""
    parser = argparse.ArgumentParser(description="Automated Backup Solution")
    parser.add_argument("-c", "--config", default="backup_config.ini", 
                      help="Path to configuration file")
    parser.add_argument("--dry-run", action="store_true",
                      help="Test run without performing actual backups")
    args = parser.parse_args()
    
    manager = BackupManager(args.config)
    
    if args.dry_run:
        print("Dry run mode - no actual backups will be performed")
        # Check configuration and validate paths
        for source_name, source_path in manager.config.items('Sources'):
            path = Path(source_path)
            if path.exists():
                print(f"✓ Source {source_name}: {source_path} (exists)")
            else:
                print(f"✗ Source {source_name}: {source_path} (does not exist)")
    else:
        manager.run_backup()


if __name__ == "__main__":
    main()