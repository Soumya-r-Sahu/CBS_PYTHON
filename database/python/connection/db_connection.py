# database/python/connection/db_connection.py
"""
Core Banking System - Database connection class
Provides a robust connection manager for direct database access.
"""

import logging
import time
import os
from pathlib import Path
import mysql.connector
from mysql.connector import Error, pooling
from contextlib import contextmanager
from colorama import init, Fore, Style

# Use centralized import system
from utils.lib.packages import fix_path
from utils.config.environment import get_environment_name, is_production, is_test, is_development, is_debug_enabled

fix_path()  # Ensures the project root is in sys.path

# Import database type manager
from utils.database_type_manager import get_database_type, get_connection_string
DYNAMIC_DB_TYPE = True

# Import database configuration
from utils.config import DATABASE_CONFIG

# Initialize colorama
init(autoreset=True)

# Set up logger
logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self, config=None):
        # Use provided config or default
        self.config = config or DATABASE_CONFIG
        self.connection_pool = None
        self.retry_count = 3
        self.retry_delay = 2  # seconds
        self._setup_connection_pool()
        
    def _setup_connection_pool(self):
        """Set up a connection pool for database access"""
        try:
            if is_debug_enabled():
                logger.debug(f"Setting up connection pool for {self.config['host']}:{self.config['port']}")
                
            # Create a connection pool
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="core_banking_pool",
                pool_size=5,
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
            )
            
            if is_debug_enabled():
                logger.debug(f"Connection pool established successfully")
                
        except Error as e:
            logger.error(f"{Fore.RED}Error creating connection pool: {e}{Style.RESET_ALL}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool with retry capability"""
        conn = None
        attempts = 0
        
        while attempts < self.retry_count:
            try:
                if not self.connection_pool:
                    logger.warning("Connection pool not initialized, attempting to recreate...")
                    self._setup_connection_pool()
                    
                conn = self.connection_pool.get_connection()
                logger.debug(f"Got connection from pool: {conn.connection_id}")
                yield conn
                break
                
            except Error as e:
                attempts += 1
                logger.error(f"{Fore.RED}Database connection error (attempt {attempts}/{self.retry_count}): {e}{Style.RESET_ALL}")
                
                if attempts < self.retry_count:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.critical(f"{Fore.RED}Failed to establish database connection after {self.retry_count} attempts{Style.RESET_ALL}")
                    raise
            finally:
                if conn and conn.is_connected():
                    conn.close()
                    logger.debug(f"Connection closed and returned to pool")

    def execute_query(self, query, params=None, fetch=True):
        """Execute a query with automatic connection management"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(query, params or ())
                
                if fetch:
                    result = cursor.fetchall()
                    return result
                else:
                    conn.commit()
                    return cursor.rowcount
            except Error as e:
                logger.error(f"{Fore.RED}Query execution error: {e}{Style.RESET_ALL}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")
                conn.rollback()
                raise
            finally:
                cursor.close()

# A global instance for common use
db_connection = DatabaseConnection()
