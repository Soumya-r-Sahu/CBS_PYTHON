#!/usr/bin/env python
"""
Utility script to update database.py to the latest version 
and run database migrations across all environments.

This script can be used to:
1. Update database models
2. Run migrations for schema changes 
3. Backup database before migrations
"""

import os
import sys
import argparse
import subprocess
import datetime
from pathlib import Path

# Add project root to path to enable imports
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

def backup_database(environment, backup_dir=None):
    """
    Create a backup of the database for the specified environment
    
    Args:
        environment: Environment name (development, production, etc)
        backup_dir: Directory to store the backup (default: Backend/database/backups)
        
    Returns:
        Path to the backup file if successful, None otherwise
    """
    if backup_dir is None:
        backup_dir = project_root / "Backend" / "database" / "backups"
        
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"db_backup_{environment}_{timestamp}.sql"
    
    print(f"Creating database backup for {environment} environment")
    print(f"Backup file: {backup_file}")
    
    # Import database configuration
    try:
        # Set environment variable to load correct config
        os.environ["CBS_ENVIRONMENT"] = environment
        
        # Import database connection
        from Backend.database.python.connection import DatabaseConnection
        db_config = DatabaseConnection().config
        
        # Build mysqldump command
        cmd = [
            "mysqldump",
            f"--host={db_config['host']}",
            f"--port={db_config['port']}",
            f"--user={db_config['user']}",
            f"--password={db_config['password']}",
            db_config['database'],
            f"--result-file={backup_file}"
        ]
        
        # Run the backup command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Backup created successfully: {backup_file}")
            return backup_file
        else:
            print(f"Error creating backup: {result.stderr}")
            return None
            
    except ImportError as e:
        print(f"Error importing database configuration: {e}")
        return None
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

def run_migration(environment, backup=True):
    """
    Run database migration for the specified environment
    
    Args:
        environment: Environment name (development, production, etc)
        backup: Whether to backup the database before migration
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Running migration for {environment} environment")
    
    # Set environment variable
    os.environ["CBS_ENVIRONMENT"] = environment
    
    # Backup database if requested
    if backup:
        backup_file = backup_database(environment)
        if not backup_file and not confirm("Backup failed. Continue with migration?"):
            return False
    
    # Import and run migration script
    try:
        # Execute migration script
        migration_script = project_root / "Backend" / "scripts" / "maintenance" / "database" / "manage_database.py"
        
        if not migration_script.exists():
            print(f"Error: Migration script not found at {migration_script}")
            return False
            
        # Run the migration script with the migrate task
        cmd = [sys.executable, str(migration_script), "--task=migrate"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Migration completed successfully for {environment}")
            print(result.stdout)
            return True
        else:
            print(f"Error during migration: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error running migration: {e}")
        return False

def confirm(message):
    """Ask for user confirmation"""
    response = input(f"{message} (y/n): ").lower()
    return response in ["y", "yes"]

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Database Migration Utility")
    
    parser.add_argument("--environments", nargs="+", default=["development"],
                      help="Environments to run migrations for (development, testing, production)")
    parser.add_argument("--no-backup", action="store_true",
                      help="Skip database backup before migration")
    parser.add_argument("--all", action="store_true",
                      help="Run migrations for all environments")
    
    args = parser.parse_args()
    
    # Determine environments to run migrations for
    environments = args.environments
    if args.all:
        environments = ["development", "testing", "production"]
    
    # Confirm production migrations
    if "production" in environments and not args.no_backup:
        print("WARNING: You are about to run migrations on the PRODUCTION environment.")
        if not confirm("Are you absolutely sure you want to continue?"):
            print("Migration aborted.")
            return
    
    # Run migrations for each environment
    results = {}
    for env in environments:
        print(f"\n{'=' * 50}")
        print(f"Running migration for {env.upper()} environment")
        print(f"{'=' * 50}")
        
        success = run_migration(env, backup=not args.no_backup)
        results[env] = "SUCCESS" if success else "FAILED"
    
    # Print summary
    print("\n" + "=" * 50)
    print("Migration Summary")
    print("=" * 50)
    for env, result in results.items():
        print(f"{env.ljust(15)}: {result}")

if __name__ == "__main__":
    main()
