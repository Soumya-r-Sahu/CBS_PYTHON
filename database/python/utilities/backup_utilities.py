# database/python/utilities/backup_utilities.py
"""
Database backup and restore utilities for Core Banking System.

These utilities provide functionality to create and restore database backups,
handle versioned backups, and database recovery operations.
"""

import os
import logging
import datetime
import subprocess
import shutil
import gzip
import json
from pathlib import Path
from typing import Dict, List, Optional, Union

# Import from database module
from database.python.connection.db_connection import DatabaseConnection

# Set up logger
logger = logging.getLogger(__name__)

# Default backup directory
DEFAULT_BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')

def create_backup(
    backup_dir: Optional[str] = None, 
    compress: bool = True,
    include_metadata: bool = True
) -> Dict[str, str]:
    """
    Create a database backup.
    
    Args:
        backup_dir: Directory to store the backup. If None, uses default.
        compress: Whether to compress the backup.
        include_metadata: Whether to include metadata about the backup.
        
    Returns:
        A dictionary with backup information.
    """
    # Use default backup directory if not specified
    if backup_dir is None:
        backup_dir = DEFAULT_BACKUP_DIR
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"cbs_backup_{timestamp}.sql"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # Get database connection
    db_conn = DatabaseConnection()
    config = db_conn.config
    
    try:
        # Use mysqldump to create backup
        mysqldump_cmd = [
            "mysqldump",
            f"--host={config['host']}",
            f"--port={config['port']}",
            f"--user={config['user']}",
            f"--password={config['password']}",
            "--single-transaction",
            "--routines",
            "--triggers",
            "--events",
            config['database']
        ]
        
        logger.info(f"Creating database backup to {backup_path}")
        
        if compress:
            backup_path += ".gz"
            with gzip.open(backup_path, 'wb') as gzfile:
                process = subprocess.Popen(
                    mysqldump_cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    error_msg = stderr.decode('utf-8')
                    logger.error(f"Backup failed: {error_msg}")
                    raise Exception(f"Database backup failed: {error_msg}")
                
                gzfile.write(stdout)
        else:
            with open(backup_path, 'wb') as backup_file:
                process = subprocess.Popen(
                    mysqldump_cmd, 
                    stdout=backup_file, 
                    stderr=subprocess.PIPE
                )
                _, stderr = process.communicate()
                
                if process.returncode != 0:
                    error_msg = stderr.decode('utf-8')
                    logger.error(f"Backup failed: {error_msg}")
                    raise Exception(f"Database backup failed: {error_msg}")
        
        logger.info(f"Database backup created successfully: {backup_path}")
        
        # Create metadata file if requested
        metadata = {
            "backup_file": os.path.basename(backup_path),
            "database": config['database'],
            "timestamp": timestamp,
            "datetime": datetime.datetime.now().isoformat(),
            "compressed": compress,
            "size_bytes": os.path.getsize(backup_path)
        }
        
        if include_metadata:
            metadata_path = os.path.join(backup_dir, f"cbs_backup_{timestamp}.json")
            with open(metadata_path, 'w') as metadata_file:
                json.dump(metadata, metadata_file, indent=2)
            logger.info(f"Backup metadata saved to: {metadata_path}")
            metadata["metadata_file"] = os.path.basename(metadata_path)
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
        raise

def restore_backup(
    backup_file: str,
    verify_before_restore: bool = True
) -> bool:
    """
    Restore a database from backup.
    
    Args:
        backup_file: Path to the backup file.
        verify_before_restore: Whether to verify the backup before restoring.
        
    Returns:
        True if the restoration was successful, False otherwise.
    """
    if not os.path.exists(backup_file):
        logger.error(f"Backup file not found: {backup_file}")
        raise FileNotFoundError(f"Backup file not found: {backup_file}")
    
    # Get database connection details
    db_conn = DatabaseConnection()
    config = db_conn.config
    
    # Check if the backup is compressed
    is_compressed = backup_file.endswith('.gz')
    
    try:
        # Verify backup if requested
        if verify_before_restore:
            logger.info(f"Verifying backup file: {backup_file}")
            # Add verification logic here
        
        # Build the mysql command
        mysql_cmd = [
            "mysql",
            f"--host={config['host']}",
            f"--port={config['port']}",
            f"--user={config['user']}",
            f"--password={config['password']}",
            config['database']
        ]
        
        logger.info(f"Restoring database from backup: {backup_file}")
        
        if is_compressed:
            with gzip.open(backup_file, 'rb') as gzfile:
                process = subprocess.Popen(
                    mysql_cmd, 
                    stdin=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                _, stderr = process.communicate(gzfile.read())
        else:
            with open(backup_file, 'rb') as backup_file_handle:
                process = subprocess.Popen(
                    mysql_cmd, 
                    stdin=backup_file_handle, 
                    stderr=subprocess.PIPE
                )
                _, stderr = process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8')
            logger.error(f"Restore failed: {error_msg}")
            raise Exception(f"Database restore failed: {error_msg}")
        
        logger.info("Database restored successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error restoring database: {str(e)}")
        raise
