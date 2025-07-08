#!/usr/bin/env python
"""
Banking Database Update Tool

This friendly utility helps you safely update the banking database structure
while preserving your data. It provides essential safety features like:

1. Automatic database backups before any changes
2. Support for multiple environments (development, testing, production)
3. Schema migration based on your latest model changes
4. Detailed logging and error reporting

Running this script is the recommended way to make any database changes.
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
    Create a safety backup of your banking database
    
    This function creates a complete backup of your database before
    any changes are made, allowing you to restore if needed.
    
    Args:
        environment: Which system to backup (development, production, etc)
        backup_dir: Where to store the backup file (creates folder if needed)
        
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
    Update your banking database schema safely
    
    This function applies all pending schema changes to your database,
    ensuring compatibility with the latest code. It first creates a backup
    (unless disabled) and provides detailed feedback on the process.
    
    Args:
        environment: Which system to update (development, production, etc)
        backup: Whether to create a safety backup first (recommended)
        
    Returns:
        True if update was successful, False if any issues occurred
    """
    print(f"Updating database schema for {environment} environment")
    
    # Set environment variable
    os.environ["CBS_ENVIRONMENT"] = environment
    
    # Backup database if requested
    if backup:
        print("Creating safety backup first...")
        backup_file = backup_database(environment)
        if not backup_file and not confirm("⚠️ Backup failed. Continue anyway? (not recommended)"):
            return False
    
    # Import and run migration script
    try:
        # Execute migration script
        migration_script = project_root / "Backend" / "scripts" / "maintenance" / "database" / "manage_database.py"
        
        if not migration_script.exists():
            print(f"❌ Error: Database manager not found at {migration_script}")
            return False
            
        # Run the migration script with the migrate task
        print("Applying schema changes...")
        cmd = [sys.executable, str(migration_script), "--task=migrate"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Database update completed successfully for {environment}")
            print(result.stdout)
            return True
        else:
            print(f"❌ Error during database update: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Unexpected error during update: {e}")
        return False

def confirm(message):
    """Ask for user confirmation with a friendly prompt"""
    response = input(f"{message} (y/n): ").lower()
    return response in ["y", "yes"]

def main():
    """Run the Banking Database Update Tool"""
    parser = argparse.ArgumentParser(
        description="Banking Database Update Tool - Safely apply schema changes"
    )
    
    parser.add_argument("--environments", nargs="+", default=["development"],
                      help="Which systems to update (development, testing, production)")
    parser.add_argument("--no-backup", action="store_true",
                      help="Skip safety backup (not recommended)")
    parser.add_argument("--all", action="store_true",
                      help="Update all environments (use with caution)")
    
    args = parser.parse_args()
    
    # Show welcome banner
    print("\n" + "=" * 60)
    print(" BANKING DATABASE UPDATE TOOL ".center(60, "="))
    print("=" * 60 + "\n")
    
    # Determine environments to run migrations for
    environments = args.environments
    if args.all:
        environments = ["development", "testing", "production"]
    
    # Confirm production migrations
    if "production" in environments and not args.no_backup:
        print("⚠️ WARNING: You are about to update the PRODUCTION database.")
        print("    This will affect the live banking system!")
        if not confirm("Are you absolutely sure you want to continue?"):
            print("Update aborted - no changes were made.")
            return
    
    # Run migrations for each environment
    results = {}
    for env in environments:
        print(f"\n{'=' * 60}")
        print(f" UPDATING {env.upper()} DATABASE ".center(60, "="))
        print(f"{'=' * 60}")
        
        success = run_migration(env, backup=not args.no_backup)
        results[env] = "✅ SUCCESS" if success else "❌ FAILED"
    
    # Print summary
    print("\n" + "=" * 60)
    print(" UPDATE SUMMARY ".center(60, "="))
    print("=" * 60)
    for env, result in results.items():
        print(f"{env.ljust(15)}: {result}")

if __name__ == "__main__":
    main()
