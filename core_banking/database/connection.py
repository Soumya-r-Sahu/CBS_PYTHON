"""
Database Connection for Core Banking System

This module provides database connection management for the Core Banking System.
"""

import os
import sys
import logging
from pathlib import Path

# Use centralized import system
from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
fix_path()  # Ensures the project root is in sys.path

# Try to import config
try:
    from core_banking.utils.config import DATABASE_CONFIG
except ImportError:
    # Fallback configuration
    DATABASE_CONFIG = {
        'user': os.environ.get('CBS_DB_USER', 'root'),
        'password': os.environ.get('CBS_DB_PASSWORD', 'password'),
        'host': os.environ.get('CBS_DB_HOST', 'localhost'),
        'port': int(os.environ.get('CBS_DB_PORT', '3306')),
        'database': os.environ.get('CBS_DB_NAME', 'core_banking')
    }

# Handle different DB engines based on availability
USE_MYSQL = None
USE_SQLITE = None
MOCK_DB = None

try:
    import pymysql
    USE_MYSQL = True
    logging.info("Using PyMySQL for database connection")
except ImportError:
    logging.warning("PyMySQL not found. Please install it using: pip install pymysql")
    USE_MYSQL = False

if not USE_MYSQL:
    try:
        import sqlite3
        USE_SQLITE = True
        logging.info("Using SQLite for database connection (fallback)")
    except ImportError:
        logging.warning("SQLite module not available")
        USE_SQLITE = False

if not USE_MYSQL and not USE_SQLITE:
    # If neither is available, try to use mock
    MOCK_DB = True
    logging.warning("No database drivers found. Will use mock connection if available")
    try:
        import mock
    except ImportError:
        logging.error("Mock module not available. Cannot create database connection.")
        MOCK_DB = False

class DatabaseConnection:
    """Database connection manager for Core Banking System"""
    
    def __init__(self, db_config=None):
        """Initialize database connection"""
        self.conn = None
        self.config = db_config or DATABASE_CONFIG
        
        # Log connection info
        host = self.config.get('host', 'localhost')
        port = self.config.get('port', 3306)
        logging.info(f"Database engine created for {host}:{port}")
        
    def get_connection(self):
        """Get a database connection"""
        if self.conn is not None:
            return self.conn
            
        try:
            if USE_MYSQL:
                self.conn = pymysql.connect(
                    host=self.config['host'],
                    user=self.config['user'],
                    password=self.config['password'],
                    database=self.config['database'],
                    charset='utf8mb4'
                )
                return self.conn
                
            elif USE_SQLITE:
                # SQLite fallback
                db_path = Path(__file__).parent.parent.parent / "data" / "core_banking.db"
                os.makedirs(db_path.parent, exist_ok=True)
                self.conn = sqlite3.connect(str(db_path))
                return self.conn
                
            elif MOCK_DB:
                # Mock connection
                try:
                    import mock
                    self.conn = mock.MagicMock()
                    return self.conn
                except ImportError:
                    logging.error("Mock module not available although it was checked earlier")
                    return None
            else:
                logging.error("No database driver available and mock not available")
                return None
                
        except Exception as e:
            logging.error(f"Database connection error: {str(e)}")
            return None
    
    def close_connection(self):
        """Close the database connection"""
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
            except Exception as e:
                logging.error(f"Error closing database connection: {str(e)}")

    def execute_query(self, query, params=None):
        """Execute a query and return the results"""
        conn = self.get_connection()
        if not conn:
            return None
            
        cursor = None
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Query execution error: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()