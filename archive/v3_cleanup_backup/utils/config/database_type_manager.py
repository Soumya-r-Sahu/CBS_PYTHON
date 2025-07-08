"""
Database Type Manager for Core Banking System

This module manages database type configurations and connections
for the Core Banking System.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Configure logger
logger = logging.getLogger(__name__)

# Default database configuration
DEFAULT_DB_CONFIG = {
    "sqlite": {
        "driver": "sqlite",
        "connection_string": "sqlite:///database/cbs.db",
        "pool_size": 5,
        "max_overflow": 10,
        "timeout": 30,
        "dialect": "sqlite"
    },
    "postgresql": {
        "driver": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "cbs_db",
        "user": "cbs_user",
        "password": "password",
        "pool_size": 10,
        "max_overflow": 20,
        "timeout": 60,
        "dialect": "postgresql"
    },
    "mysql": {
        "driver": "mysql+pymysql",
        "host": "localhost",
        "port": 3306,
        "database": "cbs_db",
        "user": "cbs_user",
        "password": "password", 
        "pool_size": 10,
        "max_overflow": 20,
        "timeout": 60,
        "dialect": "mysql"
    }
}

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DB_CONFIG_FILE = CONFIG_DIR / "db_type_config.json"

# Load database configurations from file
def load_db_config() -> Dict[str, Dict[str, Any]]:
    """
    Load database configurations from the configuration file.
    
    Returns:
        Dictionary with database configurations
    """
    config = DEFAULT_DB_CONFIG.copy()
    
    if DB_CONFIG_FILE.exists():
        try:
            with open(DB_CONFIG_FILE, "r") as f:
                file_config = json.load(f)
                
            # Update configurations with file values
            for db_type, db_config in file_config.items():
                if db_type in config:
                    config[db_type].update(db_config)
                else:
                    config[db_type] = db_config
        except Exception as e:
            logger.error(f"Error loading database configuration from {DB_CONFIG_FILE}: {str(e)}")
    
    return config

# Load database configurations
DB_CONFIGS = load_db_config()

# Determine active database type from environment or configuration
ACTIVE_DB_TYPE = os.environ.get("CBS_DATABASE_TYPE", "sqlite").lower()

# Get active database configuration
def get_active_db_config() -> Dict[str, Any]:
    """
    Get the configuration for the active database type.
    
    Returns:
        Dictionary with active database configuration
    """
    if ACTIVE_DB_TYPE not in DB_CONFIGS:
        logger.warning(f"Unknown database type '{ACTIVE_DB_TYPE}', falling back to sqlite")
        return DB_CONFIGS["sqlite"]
    
    return DB_CONFIGS[ACTIVE_DB_TYPE]

# Build connection string from configuration
def build_connection_string(db_config: Dict[str, Any]) -> str:
    """
    Build a database connection string from configuration.
    
    Args:
        db_config: Database configuration dictionary
    
    Returns:
        Connection string for the database
    """
    db_type = db_config.get("driver", "sqlite")
    
    if db_type == "sqlite":
        database = db_config.get("database", "cbs.db")
        return f"sqlite:///{database}"
    else:
        host = db_config.get("host", "localhost")
        port = db_config.get("port", 5432 if db_type == "postgresql" else 3306)
        database = db_config.get("database", "cbs_db")
        user = db_config.get("user", "cbs_user")
        password = db_config.get("password", "password")
        
        return f"{db_type}://{user}:{password}@{host}:{port}/{database}"

# Get connection string for active database
def get_connection_string() -> str:
    """
    Get the connection string for the active database.
    
    Returns:
        Connection string for the active database
    """
    db_config = get_active_db_config()
    
    # If connection string is explicitly defined, use it
    if "connection_string" in db_config:
        return db_config["connection_string"]
    
    # Otherwise, build from components
    return build_connection_string(db_config)

# Check if database supports a specific feature
def db_supports_feature(feature: str) -> bool:
    """
    Check if the active database supports a specific feature.
    
    Args:
        feature: Feature to check support for
    
    Returns:
        True if the feature is supported, False otherwise
    """
    db_config = get_active_db_config()
    db_type = db_config.get("dialect", ACTIVE_DB_TYPE)
    
    feature_support = {
        "transactions": ["postgresql", "mysql"],  # SQLite has limited transaction support
        "foreign_keys": ["postgresql", "mysql", "sqlite"],
        "json": ["postgresql", "mysql"],  # SQLite has limited JSON support
        "array": ["postgresql"],
        "full_text_search": ["postgresql", "mysql"],  # SQLite has limited FTS support
        "schema": ["postgresql", "mysql"],
        "stored_procedures": ["postgresql", "mysql"],
        "triggers": ["postgresql", "mysql", "sqlite"],
        "views": ["postgresql", "mysql", "sqlite"],
        "materialized_views": ["postgresql"],
        "partitioning": ["postgresql", "mysql"],
        "uuid": ["postgresql"],
        "enum": ["postgresql", "mysql"]
    }
    
    return db_type in feature_support.get(feature, [])

# Get database-specific SQL syntax
def get_db_specific_sql(sql_type: str, params: Dict[str, Any] = None) -> str:
    """
    Get database-specific SQL syntax.
    
    Args:
        sql_type: Type of SQL syntax to get
        params: Parameters for the SQL syntax
    
    Returns:
        Database-specific SQL syntax
    """
    db_config = get_active_db_config()
    db_type = db_config.get("dialect", ACTIVE_DB_TYPE)
    params = params or {}
    
    # Define SQL syntax for different database types
    sql_syntax = {
        "limit_offset": {
            "postgresql": "LIMIT {limit} OFFSET {offset}",
            "mysql": "LIMIT {offset}, {limit}",
            "sqlite": "LIMIT {limit} OFFSET {offset}"
        },
        "boolean": {
            "postgresql": "BOOLEAN",
            "mysql": "TINYINT(1)",
            "sqlite": "INTEGER"
        },
        "current_timestamp": {
            "postgresql": "CURRENT_TIMESTAMP",
            "mysql": "CURRENT_TIMESTAMP()",
            "sqlite": "CURRENT_TIMESTAMP"
        },
        "text": {
            "postgresql": "TEXT",
            "mysql": "LONGTEXT",
            "sqlite": "TEXT"
        },
        "uuid": {
            "postgresql": "UUID",
            "mysql": "CHAR(36)",
            "sqlite": "TEXT"
        },
        "json": {
            "postgresql": "JSONB",
            "mysql": "JSON",
            "sqlite": "TEXT"
        },
        "create_index": {
            "postgresql": "CREATE INDEX idx_{table}_{column} ON {table}({column})",
            "mysql": "CREATE INDEX idx_{table}_{column} ON {table}({column})",
            "sqlite": "CREATE INDEX idx_{table}_{column} ON {table}({column})"
        }
    }
    
    if sql_type not in sql_syntax:
        raise ValueError(f"Unknown SQL syntax type: {sql_type}")
    
    syntax_template = sql_syntax[sql_type].get(db_type, sql_syntax[sql_type]["sqlite"])
    return syntax_template.format(**params)

# List available database types
def list_available_db_types() -> List[str]:
    """
    List available database types.
    
    Returns:
        List of available database types
    """
    return list(DB_CONFIGS.keys())

# Validate database configuration
def validate_db_config(db_type: str = None) -> Dict[str, Any]:
    """
    Validate database configuration for a specific type.
    
    Args:
        db_type: Database type to validate (defaults to active type)
    
    Returns:
        Dictionary with validation results
    """
    db_type = db_type or ACTIVE_DB_TYPE
    
    if db_type not in DB_CONFIGS:
        return {
            "valid": False,
            "errors": [f"Unknown database type: {db_type}"]
        }
    
    db_config = DB_CONFIGS[db_type]
    errors = []
    
    # Required fields for each database type
    required_fields = {
        "sqlite": ["driver"],
        "postgresql": ["driver", "host", "port", "database", "user", "password"],
        "mysql": ["driver", "host", "port", "database", "user", "password"]
    }
    
    # Check required fields
    for field in required_fields.get(db_type, []):
        if field not in db_config:
            errors.append(f"Missing required field: {field}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

# Check if database connection is valid
def test_db_connection(db_type: str = None) -> Dict[str, Any]:
    """
    Test database connection.
    
    Args:
        db_type: Database type to test (defaults to active type)
    
    Returns:
        Dictionary with test results
    """
    db_type = db_type or ACTIVE_DB_TYPE
    
    # Validate configuration first
    validation = validate_db_config(db_type)
    if not validation["valid"]:
        return {
            "success": False,
            "message": "Invalid configuration",
            "errors": validation["errors"]
        }
    
    # Get connection string
    if db_type == ACTIVE_DB_TYPE:
        connection_string = get_connection_string()
    else:
        db_config = DB_CONFIGS[db_type]
        if "connection_string" in db_config:
            connection_string = db_config["connection_string"]
        else:
            connection_string = build_connection_string(db_config)
    
    # Test connection
    try:
        import sqlalchemy
        engine = sqlalchemy.create_engine(connection_string)
        connection = engine.connect()
        connection.close()
        
        return {
            "success": True,
            "message": f"Successfully connected to {db_type} database"
        }
    except ImportError:
        return {
            "success": False,
            "message": "SQLAlchemy not installed",
            "errors": ["SQLAlchemy is required for database connection testing"]
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to connect to {db_type} database",
            "errors": [str(e)]
        }
