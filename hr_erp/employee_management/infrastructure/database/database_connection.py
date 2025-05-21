"""
Database Connection Module

This module provides a database connection for the HR-ERP system's infrastructure layer.
"""

import logging
from typing import Any, Optional

# Try importing from main database connection
try:
    from utils.lib.packages import fix_path, import_module
    fix_path()  # Ensures project root is in sys.path
    DatabaseConnection = import_module("database.python.connection").DatabaseConnection
except ImportError:
    # Fallback implementation if the centralized database module is not available
    import mysql.connector
    from mysql.connector import Error
    
    class DatabaseConnection:
        """
        Database connection manager
        
        This class manages connections to the MySQL database for the HR-ERP system.
        If the centralized database connection module is available, it delegates to that.
        Otherwise, it provides a basic implementation.
        """
        
        def __init__(self, db_config=None):
            """
            Initialize the database connection manager
            
            Args:
                db_config: Database configuration dictionary
            """
            self._logger = logging.getLogger('hr-database')
            self._connection = None
            self._config = db_config
            
            if not self._config:
                # Try to import from config
                try:
                    try:
                        # Try relative import if config.py is in the same package or parent package
                        from ...config import DATABASE_CONFIG
                        self._config = DATABASE_CONFIG
                    except (ImportError, ValueError):
                        self._config = {
                            'host': 'localhost',
                            'database': 'CBS_PYTHON',
                            'user': 'root',
                            'password': '',
                            'port': 3307
                        }
                except ImportError:
                    # Default configuration
                    self._config = {
                        'host': 'localhost',
                        'database': 'CBS_PYTHON',
                        'user': 'root',
                        'password': '',
                        'port': 3307
                    }
        
        def get_connection(self) -> Optional[Any]:
            """
            Get a connection to the database
            
            Returns:
                Database connection object or None if connection fails
            """
            if self._connection and self._connection.is_connected():
                return self._connection
                
            try:
                self._connection = mysql.connector.connect(
                    host=self._config['host'],
                    database=self._config['database'],
                    user=self._config['user'],
                    password=self._config['password'],
                    port=self._config['port']
                )
                
                if self._connection.is_connected():
                    self._logger.info("Database connection established")
                    return self._connection
                    
            except Error as e:
                self._logger.error(f"Error connecting to database: {e}")
                
            return None
        
        def close_connection(self) -> None:
            """Close the database connection"""
            if self._connection and self._connection.is_connected():
                self._connection.close()
                self._logger.info("Database connection closed")
