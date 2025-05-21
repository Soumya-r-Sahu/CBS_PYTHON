"""
Database Type Manager for Core Banking System

This module provides functionality to dynamically switch between different database types
(MySQL, SQLite, PostgreSQL) in the Core Banking System. It includes a configuration 
storage mechanism to persist the selected database type across restarts.

Usage:
------
from utils.config.database_type_manager import DatabaseTypeManager

# Get current database type
db_type = DatabaseTypeManager.get_database_type()

# Change database type
DatabaseTypeManager.set_database_type('postgresql')

# Get connection string for current database type
conn_string = DatabaseTypeManager.get_connection_string()
"""

import os
import json
import logging
from pathlib import Path
from utils.design_patterns import singleton
from utils.config.config import DATABASE_CONFIG

# Set up logger
logger = logging.getLogger(__name__)

# Database type constants
DB_TYPE_MYSQL = 'mysql'
DB_TYPE_SQLITE = 'sqlite'
DB_TYPE_POSTGRESQL = 'postgresql'

# Valid database types
VALID_DB_TYPES = [DB_TYPE_MYSQL, DB_TYPE_SQLITE, DB_TYPE_POSTGRESQL]

@singleton
class DatabaseTypeManager:
    """
    Manages database type selection and configuration for the Core Banking System.
    Implements the singleton pattern to ensure consistency across the application.
    """
    
    def __init__(self):
        """Initialize the database type manager"""
        self.config_path = self._get_config_path()
        self.current_db_type = self._load_db_type()
        logger.info(f"Database Type Manager initialized with type: {self.current_db_type}")
    
    def _get_config_path(self):
        """Get the path to the database configuration file"""
        # Use the config directory if it exists, otherwise use the current directory
        config_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent / "config"
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "db_type_config.json"
    
    def _load_db_type(self):
        """Load the database type from the configuration file"""
        # Default to MySQL if no configuration exists
        default_type = DB_TYPE_MYSQL
        
        if not self.config_path.exists():
            # Create default configuration
            self._save_db_type(default_type)
            return default_type
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                db_type = config.get('db_type', default_type)
                
                # Validate the loaded type
                if db_type not in VALID_DB_TYPES:
                    logger.warning(f"Invalid database type in config: {db_type}. Using default: {default_type}")
                    return default_type
                
                return db_type
        except Exception as e:
            logger.error(f"Error loading database type configuration: {e}")
            return default_type
    
    def _save_db_type(self, db_type):
        """Save the database type to the configuration file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump({'db_type': db_type}, f)
            logger.info(f"Database type configuration saved: {db_type}")
        except Exception as e:
            logger.error(f"Error saving database type configuration: {e}")
    
    def get_database_type(self):
        """Get the current database type"""
        return self.current_db_type
    
    def set_database_type(self, db_type):
        """Set the database type"""
        if db_type not in VALID_DB_TYPES:
            raise ValueError(f"Invalid database type: {db_type}. Valid types: {', '.join(VALID_DB_TYPES)}")
        
        self.current_db_type = db_type
        self._save_db_type(db_type)
        logger.info(f"Database type changed to: {db_type}")
        return True
    
    def get_connection_string(self):
        """Get the connection string for the current database type"""
        db_type = self.current_db_type
        
        if db_type == DB_TYPE_SQLITE:
            # Create data directory if it doesn't exist
            data_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "cbs_python.db"
            return f"sqlite:///{db_path}"
        
        elif db_type == DB_TYPE_MYSQL:
            # Use the existing MySQL configuration
            host = DATABASE_CONFIG.get('host', 'localhost')
            port = DATABASE_CONFIG.get('port', 3306)
            user = DATABASE_CONFIG.get('user', 'root')
            password = DATABASE_CONFIG.get('password', '')
            database = DATABASE_CONFIG.get('database', 'CBS_PYTHON')
            
            return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
        
        elif db_type == DB_TYPE_POSTGRESQL:
            # Use PostgreSQL configuration or fallback to environment variables
            host = os.environ.get('CBS_PG_HOST', DATABASE_CONFIG.get('pg_host', 'localhost'))
            port = os.environ.get('CBS_PG_PORT', DATABASE_CONFIG.get('pg_port', 5432))
            user = os.environ.get('CBS_PG_USER', DATABASE_CONFIG.get('pg_user', 'postgres'))
            password = os.environ.get('CBS_PG_PASSWORD', DATABASE_CONFIG.get('pg_password', 'postgres'))
            database = os.environ.get('CBS_PG_DB', DATABASE_CONFIG.get('pg_database', 'CBS_PYTHON'))
            
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        # If we somehow get here with an invalid type
        raise ValueError(f"Unsupported database type: {db_type}")

# Create a singleton instance for ease of use
db_type_manager = DatabaseTypeManager()

# Convenience functions
def get_database_type():
    """Get the current database type"""
    return db_type_manager.get_database_type()

def set_database_type(db_type):
    """Set the database type"""
    return db_type_manager.set_database_type(db_type)

def get_connection_string():
    """Get the connection string for the current database type"""
    return db_type_manager.get_connection_string()
