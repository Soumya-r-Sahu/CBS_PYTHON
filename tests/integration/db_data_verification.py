"""
Database Data Verification Utilities

This module provides utilities for verifying database data
to support the Core Banking System integration tests.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.lib.packages import import_module
            DatabaseConnection = import_module("database.python.connection").DatabaseConnection


def check_table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    return cursor.fetchone() is not None


def count_records(cursor, table_name):
    """Count records in a table"""
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cursor.fetchone()[0]


def verify_sample_data():
    """Verify that sample data is properly loaded in the database"""
    print("Verifying Core Banking System database data...")
    
    # Connect to database
    db = DatabaseConnection()
    conn = db.get_connection()
    
    if not conn or not hasattr(conn, 'is_connected') or not conn.is_connected():
        print("ERROR: Could not connect to the database!")
        print("Please ensure MySQL is running and check your connection settings in utils/config.py")
        return False, {}
    
    # Create cursor
    cursor = conn.cursor()
    
    # Tables to verify
    tables = [
        "customers",
        "accounts",
        "transactions",
        "upi_users",
        "upi_transactions",
        "cards"
    ]
    
    results = {}
    
    # Check each table
    for table in tables:
        if check_table_exists(cursor, table):
            count = count_records(cursor, table)
            print(f"Table '{table}': {count} records")
            results[table] = count
        else:
            print(f"Table '{table}' does not exist!")
            results[table] = 0
    
    # Close database connection
    cursor.close()
    conn.close()
    
    # Check if we have data in essential tables
    essential_tables = ["customers", "accounts"]
    all_have_data = all(results.get(table, 0) > 0 for table in essential_tables)
    
    return all_have_data, results


def verify_specific_record(table, column, value):
    """Verify that a specific record exists in the database"""
    # Connect to database
    db = DatabaseConnection()
    conn = db.get_connection()
    
    if not conn or not hasattr(conn, 'is_connected') or not conn.is_connected():
        print("ERROR: Could not connect to the database!")
        return False
    
    # Create cursor
    cursor = conn.cursor()
    
    # Check if the table exists
    if not check_table_exists(cursor, table):
        print(f"Table '{table}' does not exist!")
        conn.close()
        return False
    
    # Query for the record
    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} = %s", (value,))
    count = cursor.fetchone()[0]
    
    # Close database connection
    cursor.close()
    conn.close()
    
    return count > 0


if __name__ == "__main__":
    success, results = verify_sample_data()
    sys.exit(0 if success else 1)
