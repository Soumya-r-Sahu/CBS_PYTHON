"""
Banking System Database Manager

This script provides tools to manage the Core Banking System database, 
including schema migrations, data updates, and regular maintenance tasks.
It works across all environments (development, testing, production).
"""
import os
import sys
import argparse
from pathlib import Path
import importlib
import datetime

# Add project root to path to enable imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import database modules
try:
    from database.python.models import Base, engine, initialize_database
except ImportError:
    print("Error: Could not import database models")
    print("Make sure database/python/models.py exists and is properly configured")
    sys.exit(1)

def run_migration(verbose=False):
    """
    Apply database schema changes and create missing tables
    
    This function ensures the database structure matches the SQLAlchemy models
    by creating missing tables and relationships. It doesn't modify existing data.
    
    Args:
        verbose: Whether to print detailed information during migration
    
    Returns:
        True if migration was successful, False otherwise
    """
    print("Running database migration...")
    try:
        # Create all tables defined in Base
        Base.metadata.create_all(engine)
        print("Migration completed successfully")
        
        # Initialize default data if needed
        if initialize_database():
            print("Database initialized with default data")
        else:
            print("Database initialization skipped or failed")
            
        # Log migration
        with open(os.path.join(current_dir, "migration_history.log"), "a") as log:
            log.write(f"{datetime.datetime.now()} - Migration executed\n")
            
        return True
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

def run_maintenance(backup=True, optimize=True, verbose=False):
    """
    Perform database maintenance tasks
    
    Args:
        backup: Whether to backup the database before maintenance
        optimize: Whether to optimize the database
        verbose: Whether to print detailed information
    """
    print("Performing database maintenance...")
    
    if backup:
        if _backup_database():
            print("Database backup created successfully")
        else:
            print("Database backup failed")
            if input("Continue with maintenance? (y/n): ").lower() != 'y':
                return False
    
    if optimize:
        if _optimize_database():
            print("Database optimization completed")
        else:
            print("Database optimization failed")
    
    # Log maintenance
    with open(os.path.join(current_dir, "maintenance_history.log"), "a") as log:
        log.write(f"{datetime.datetime.now()} - Maintenance executed\n")
        
    return True

def _backup_database():
    """Create a backup of the database"""
    try:
        from database.python.connection import DatabaseConnection
        db = DatabaseConnection()
        conn = db.get_connection()
        
        # Create backups directory if it doesn't exist
        backup_dir = os.path.join(project_root, "Backend", "database", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"db_backup_{timestamp}.sql")
        
        # Execute backup command (implementation depends on database type)
        # For MySQL/MariaDB:
        print(f"Backing up database to {backup_path}")
        os.system(f"mysqldump -u {db.config['user']} -p{db.config['password']} {db.config['database']} > {backup_path}")
        
        return True
    except Exception as e:
        print(f"Backup error: {e}")
        return False

def _optimize_database():
    """Optimize database tables"""
    try:
        from database.python.connection import DatabaseConnection
        db = DatabaseConnection()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        # Optimize each table
        for table in tables:
            table_name = table[0]
            print(f"Optimizing table: {table_name}")
            cursor.execute(f"OPTIMIZE TABLE {table_name}")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Optimization error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database management tool")
    parser.add_argument("--task", choices=["migrate", "maintain"], 
                      help="Task to perform: migrate or maintain")
    parser.add_argument("--verbose", action="store_true", 
                      help="Enable verbose output")
    parser.add_argument("--no-backup", action="store_true", 
                      help="Skip database backup during maintenance")
    parser.add_argument("--no-optimize", action="store_true", 
                      help="Skip database optimization during maintenance")
    
    args = parser.parse_args()
    
    # If no arguments provided, prompt user
    if not args.task:
        task = input("Enter task (migrate/maintain): ").strip().lower()
    else:
        task = args.task
    
    if task == "migrate":
        success = run_migration(verbose=args.verbose)
    elif task == "maintain":
        success = run_maintenance(
            backup=not args.no_backup,
            optimize=not args.no_optimize,
            verbose=args.verbose
        )
    else:
        print("Invalid task. Please choose 'migrate' or 'maintain'.")
        sys.exit(1)
    
    sys.exit(0 if success else 1)
