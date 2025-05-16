"""
Database Helper for Core Banking System

This module provides utility functions for working with the Core Banking database.
"""

import os
import sys
from pathlib import Path

# Use centralized import system
from utils.lib.packages import fix_path, import_module
fix_path()  # Ensures the project root is in sys.path

try:
    from core_banking.database.connection import DatabaseConnection
except ImportError:
    # Try legacy path
    try:
        DatabaseConnection = import_module("database.python.connection").DatabaseConnection
    except ImportError:
        # Create placeholder if unavailable
        class DatabaseConnection:
            def __init__(self):
                print("WARNING: Using mock database connection")
                self.conn = None
            
            def get_connection(self):
                return self.conn
                
            def close_connection(self):
                pass


def get_database_connection():
    """Get a database connection using appropriate configuration"""
    return DatabaseConnection().get_connection()


def execute_query(query, params=None, fetch_all=True):
    """
    Execute a database query
    
    Args:
        query (str): SQL query to execute
        params (tuple, optional): Parameters for the query
        fetch_all (bool): If True, fetches all rows, otherwise just first row
        
    Returns:
        List of results or single result depending on fetch_all
    """
    conn = get_database_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch_all:
            return cursor.fetchall()
        else:
            return cursor.fetchone()
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()


def execute_transaction(queries):
    """
    Execute multiple queries in a transaction
    
    Args:
        queries (list): List of (query, params) tuples
        
    Returns:
        bool: True if transaction succeeded, False otherwise
    """
    conn = get_database_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        conn.autocommit = False
        
        for query, params in queries:
            cursor.execute(query, params or ())
            
        conn.commit()
        return True
    except Exception as e:
        print(f"Transaction error: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if conn:
            conn.autocommit = True
