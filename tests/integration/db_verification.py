"""
Database Utilities for Testing

This module provides utilities for database verification and setup
to support the Core Banking System integration tests.
"""

import sys
import os
import time
import mysql.connector
from mysql.connector import Error

# Add parent directory to path

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment, get_database_connection
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


try:
    from utils.config.config import DATABASE_CONFIG
except ImportError:
    print("Could not import database config, using default values")
    DATABASE_CONFIG = {
        'host': 'localhost',
        'database': 'core_banking_system',
        'user': 'root',
        'password': '',
        'port': 3306
    }

def print_header(text):
    """Print a formatted header"""
    width = 60
    print("\n" + "=" * width)
    print(f"{text.center(width)}")
    print("=" * width + "\n")


def connect_to_mysql():
    """Connect to MySQL server without specifying a database"""
    try:
        # Connect without specifying a database
        config = DATABASE_CONFIG.copy()
        if 'database' in config:
            del config['database']
        
        conn = mysql.connector.connect(**config)
        print("✅ Connected to MySQL server successfully")
        return conn
    except Error as e:
        print(f"❌ Error connecting to MySQL server: {e}")
        return None


def check_database_exists(conn, db_name):
    """Check if the database exists"""
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    databases = [x[0] for x in cursor.fetchall()]
    
    if db_name in databases:
        print(f"✅ Database '{db_name}' exists")
        return True
    else:
        print(f"❌ Database '{db_name}' does not exist")
        return False


def create_database(conn, db_name):
    """Create the database if it doesn't exist"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"✅ Database '{db_name}' created successfully")
        return True
    except Error as e:
        print(f"❌ Error creating database: {e}")
        return False


def connect_to_database():
    """Connect to the specific database"""
    try:
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        print(f"✅ Connected to '{DATABASE_CONFIG['database']}' database successfully")
        return conn
    except Error as e:
        print(f"❌ Error connecting to database: {e}")
        return None


def check_tables(conn):
    """Check if the required tables exist"""
    tables = [
        'accounts', 'customers', 'transactions', 'users',
        'upi_users', 'upi_transactions', 'cards'
    ]
    
    existing_tables = []
    missing_tables = []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        existing_tables = [x[0] for x in cursor.fetchall()]
        
        for table in tables:
            if table in existing_tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' does not exist")
                missing_tables.append(table)
        
        return missing_tables
    except Error as e:
        print(f"❌ Error checking tables: {e}")
        return tables  # Assume all are missing if there's an error


def check_stored_procedures(conn):
    """Check if stored procedures exist"""
    procedures = []
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW PROCEDURE STATUS WHERE Db = %s", (DATABASE_CONFIG['database'],))
        procedures = [x[1] for x in cursor.fetchall()]
        
        if procedures:
            print(f"✅ Found {len(procedures)} stored procedures:")
            for proc in procedures:
                print(f"  - {proc}")
        else:
            print("❌ No stored procedures found")
        
        return procedures
    except Error as e:
        print(f"❌ Error checking stored procedures: {e}")
        return procedures


def verify_database_setup():
    """Verify the database setup and return status"""
    print_header("Core Banking System - Database Setup Verification")
    
    # Step 1: Connect to MySQL server
    print("Step 1: Connecting to MySQL server")
    conn = connect_to_mysql()
    if not conn:
        print("Cannot proceed without MySQL connection")
        return False, None, None
    
    # Step 2: Check if database exists
    print("\nStep 2: Checking if database exists")
    db_name = DATABASE_CONFIG['database']
    db_exists = check_database_exists(conn, db_name)
    
    # Step 3: Create database if it doesn't exist
    if not db_exists:
        print("\nStep 3: Creating database")
        if not create_database(conn, db_name):
            conn.close()
            return False, None, None
    else:
        print("\nStep 3: Database already exists, skipping creation")
    
    conn.close()
    
    # Step 4: Connect to the database
    print("\nStep 4: Connecting to the database")
    db_conn = connect_to_database()
    if not db_conn:
        print("Cannot proceed without database connection")
        return False, None, None
    
    # Step 5: Check if tables exist
    print("\nStep 5: Checking if tables exist")
    missing_tables = check_tables(db_conn)
    tables_ok = len(missing_tables) == 0
    
    # Step 6: Check if stored procedures exist
    print("\nStep 6: Checking if stored procedures exist")
    procedures = check_stored_procedures(db_conn)
    procedures_ok = len(procedures) > 0
    
    db_conn.close()
    
    # Final status
    print_header("Database Setup Verification Summary")
    print(f"Database: {'✅' if db_exists else '❌'}")
    print(f"Tables: {'✅' if tables_ok else '❌'}")
    print(f"Stored Procedures: {'✅' if procedures_ok else '❌'}")
    
    return db_exists and tables_ok and procedures_ok, missing_tables, procedures


if __name__ == "__main__":
    success, missing_tables, procedures = verify_database_setup()
    sys.exit(0 if success else 1)