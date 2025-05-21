"""
Centralized Database Operations

This module provides standardized database operations for all modules.
It serves as a centralization point for common database functions.
"""

import os
import datetime
import logging
from contextlib import contextmanager

# Try to import the specific database types
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

# Import service registry for module registration
from utils.lib.service_registry import ServiceRegistry

# Configure logger
logger = logging.getLogger(__name__)

class DatabaseOperations:
    """
    Centralized database operations for all modules.
    
    Description:
        This class provides standardized database operations that can be used
        across all modules. It supports multiple database backends through
        adapters and provides common operations like querying, executing
        transactions, and managing connections.
    
    Usage:
        # Get an instance with default configuration
        db_ops = DatabaseOperations.get_instance()
        
        # Execute a query
        results = db_ops.execute_query("SELECT * FROM customers WHERE status = %s", ["active"])
        
        # Execute in transaction
        with db_ops.transaction():
            db_ops.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", [100.50, "ACC001"])
            db_ops.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", [100.50, "ACC002"])
    """
    
    _instances = {}
    
    @classmethod
    def get_instance(cls, connection_name="default"):
        """
        Get a database operations instance for the specified connection
        
        Args:
            connection_name (str): The named connection to use
            
        Returns:
            DatabaseOperations: Instance configured for the connection
        """
        if connection_name not in cls._instances:
            cls._instances[connection_name] = cls(connection_name)
        return cls._instances[connection_name]
    
    def __init__(self, connection_name="default"):
        """
        Initialize database operations with a connection name
        
        Args:
            connection_name (str): The named connection to use
        """
        self.connection_name = connection_name
        self.connection = None
        self._load_configuration()
    
    def _load_configuration(self):
        """Load database configuration from settings"""
        try:
            # For future enhancement: Load from unified config system
            from database.python.common.database_operations import get_connection_config
            self.config = get_connection_config(self.connection_name)
        except ImportError:
            logger.warning("Could not load connection configuration, using defaults")
            self.config = {
                "type": "sqlite",
                "database": ":memory:",
                "autocommit": False
            }
    
    def connect(self):
        """
        Establish a database connection
        
        Returns:
            bool: True if connection successful
        """
        if self.connection:
            return True
            
        db_type = self.config.get("type", "sqlite").lower()
        
        try:
            if db_type == "postgres" and POSTGRES_AVAILABLE:
                self.connection = psycopg2.connect(
                    host=self.config.get("host", "localhost"),
                    database=self.config.get("database", "postgres"),
                    user=self.config.get("user", "postgres"),
                    password=self.config.get("password", ""),
                    port=self.config.get("port", 5432)
                )
            elif db_type == "mysql" and MYSQL_AVAILABLE:
                self.connection = mysql.connector.connect(
                    host=self.config.get("host", "localhost"),
                    database=self.config.get("database", "mysql"),
                    user=self.config.get("user", "root"),
                    password=self.config.get("password", ""),
                    port=self.config.get("port", 3306)
                )
            elif SQLITE_AVAILABLE:
                db_path = self.config.get("database", ":memory:")
                self.connection = sqlite3.connect(db_path)
                # Enable foreign key constraints
                self.connection.execute("PRAGMA foreign_keys = ON")
            else:
                logger.error(f"Database type {db_type} not available")
                return False
                
            if self.config.get("autocommit", False):
                if db_type == "postgres":
                    self.connection.autocommit = True
                elif db_type == "mysql":
                    self.connection.autocommit = True
                    
            logger.info(f"Connected to {db_type} database")
            return True
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            return False
    
    def disconnect(self):
        """Close the database connection"""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}")
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions
        
        Usage:
            with db_ops.transaction():
                db_ops.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 'ACC001'")
                db_ops.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 'ACC002'")
                
        Raises:
            Exception: Any exception that occurs during the transaction
        """
        if not self.connection and not self.connect():
            raise Exception("Could not establish database connection")
            
        try:
            yield self
            self.connection.commit()
            logger.debug("Transaction committed")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Transaction rolled back: {str(e)}")
            raise
    
    def execute(self, query, params=None):
        """
        Execute a query with no results expected
        
        Args:
            query (str): SQL query to execute
            params (list, optional): Parameters for the query
            
        Returns:
            int: Number of rows affected
        
        Raises:
            Exception: If execution fails
        """
        if not self.connection and not self.connect():
            raise Exception("Could not establish database connection")
            
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or [])
            affected = cursor.rowcount
            if not self.config.get("autocommit", False):
                self.connection.commit()
            return affected
        except Exception as e:
            if not self.config.get("autocommit", False):
                self.connection.rollback()
            logger.error(f"Error executing query: {str(e)}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query, params=None, as_dict=True):
        """
        Execute a query and return results
        
        Args:
            query (str): SQL query to execute
            params (list, optional): Parameters for the query
            as_dict (bool): Return results as dictionaries
            
        Returns:
            list: Query results
            
        Raises:
            Exception: If query fails
        """
        if not self.connection and not self.connect():
            raise Exception("Could not establish database connection")
            
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or [])
            
            if as_dict:
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
        finally:
            cursor.close()
    
    def execute_batch(self, query, params_list):
        """
        Execute a batch of queries with the same SQL but different parameters
        
        Args:
            query (str): SQL query to execute
            params_list (list): List of parameter lists
            
        Returns:
            int: Number of rows affected
            
        Raises:
            Exception: If execution fails
        """
        if not self.connection and not self.connect():
            raise Exception("Could not establish database connection")
            
        cursor = self.connection.cursor()
        total_affected = 0
        
        try:
            for params in params_list:
                cursor.execute(query, params)
                total_affected += cursor.rowcount
                
            if not self.config.get("autocommit", False):
                self.connection.commit()
                
            return total_affected
        except Exception as e:
            if not self.config.get("autocommit", False):
                self.connection.rollback()
            logger.error(f"Error executing batch: {str(e)}")
            raise
        finally:
            cursor.close()

# Register database operations with service registry
def register_database_services():
    """Register database services with the service registry"""
    registry = ServiceRegistry()
    
    # Register default database operations
    db_ops = DatabaseOperations.get_instance()
    registry.register("database.operations", db_ops, "database")
    
    # Register fallback operations
    class FallbackDatabaseOps:
        """Fallback database operations when the database module is unavailable"""
        def execute_query(self, query, params=None, as_dict=True):
            logger.warning("Using fallback database operations")
            return []
            
        def execute(self, query, params=None):
            logger.warning("Using fallback database operations")
            return 0
            
        @contextmanager
        def transaction(self):
            logger.warning("Using fallback database operations")
            try:
                yield self
            except Exception:
                raise
    
    registry.register_fallback("database.operations", FallbackDatabaseOps())
    
    logger.info("Database services registered")

# Initialize registration on module import
register_database_services()
