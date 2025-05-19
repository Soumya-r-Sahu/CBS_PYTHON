"""
Core Banking System Configuration

This module provides access to configuration settings used throughout the system.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Union, Optional

# Configure logger
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "database": {
        "type": "sqlite",  # sqlite, postgresql, mysql
        "host": "localhost",
        "port": 5432,
        "name": "cbs_db",
        "user": "cbs_user",
        "password": "password"
    },
    "api": {
        "host": "0.0.0.0",
        "port": 5000,
        "debug": False,
        "timeout": 30,
        "rate_limit": 100
    },
    "security": {
        "jwt_secret": "development-secret-key",
        "jwt_expiry_minutes": 60,
        "password_min_length": 8,
        "password_require_special": True,
        "password_require_numbers": True,
        "password_require_uppercase": True,
        "max_login_attempts": 5,
        "lockout_duration_minutes": 30
    },
    "logging": {
        "level": "INFO",
        "file": "cbs_system.log",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "max_size_mb": 10,
        "backup_count": 5
    },
    "email": {
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "from_address": "noreply@example.com",
        "use_tls": True
    },
    "paths": {
        "templates": "templates",
        "static": "static",
        "uploads": "uploads",
        "exports": "exports",
        "temp": "temp"
    },
    "features": {
        "multi_currency": False,
        "scheduled_payments": True,
        "notifications": True,
        "audit_trail": True,
        "reports": True
    }
}

# Determine environment
ENVIRONMENT = os.environ.get("CBS_ENVIRONMENT", "development").lower()
DEBUG = os.environ.get("CBS_DEBUG", "False").lower() in ("true", "1", "yes")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
ENV_CONFIG_FILE = CONFIG_DIR / f"{ENVIRONMENT}.yaml"
LOCAL_CONFIG_FILE = CONFIG_DIR / "local.yaml"

# Load configuration from files
config = DEFAULT_CONFIG.copy()

def load_config_file(file_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a file.
    
    Args:
        file_path: Path to the configuration file
    
    Returns:
        Dictionary with configuration values
    """
    if not file_path.exists():
        logger.warning(f"Configuration file not found: {file_path}")
        return {}
    
    try:
        with open(file_path, "r") as f:
            if file_path.suffix.lower() in (".yaml", ".yml"):
                return yaml.safe_load(f) or {}
            elif file_path.suffix.lower() == ".json":
                return json.load(f)
            else:
                logger.warning(f"Unsupported configuration file format: {file_path}")
                return {}
    except Exception as e:
        logger.error(f"Error loading configuration from {file_path}: {str(e)}")
        return {}

# Load environment-specific configuration
env_config = load_config_file(ENV_CONFIG_FILE)
for section, values in env_config.items():
    if section in config and isinstance(values, dict):
        config[section].update(values)
    else:
        config[section] = values

# Load local configuration (highest priority, git-ignored)
local_config = load_config_file(LOCAL_CONFIG_FILE)
for section, values in local_config.items():
    if section in config and isinstance(values, dict):
        config[section].update(values)
    else:
        config[section] = values

# Override with environment variables
for section in config:
    for key in config[section]:
        env_var = f"CBS_{section.upper()}_{key.upper()}"
        if env_var in os.environ:
            value = os.environ[env_var]
            
            # Convert to appropriate type
            current_value = config[section][key]
            if isinstance(current_value, bool):
                config[section][key] = value.lower() in ("true", "1", "yes")
            elif isinstance(current_value, int):
                config[section][key] = int(value)
            elif isinstance(current_value, float):
                config[section][key] = float(value)
            else:
                config[section][key] = value

# Export common variables
DATABASE_CONFIG = config["database"]
API_CONFIG = config["api"]
SECURITY_CONFIG = config["security"]
LOGGING_CONFIG = config["logging"]
EMAIL_CONFIG = config["email"]
PATHS_CONFIG = config["paths"]
FEATURES_CONFIG = config["features"]

# Utility functions for accessing configuration
def get_config_value(section: str, key: str, default: Any = None) -> Any:
    """
    Get a configuration value, with fallback to default if not found.
    
    Args:
        section: Configuration section
        key: Configuration key
        default: Default value if not found
    
    Returns:
        Configuration value or default
    """
    return config.get(section, {}).get(key, default)

def get_nested_config_value(path: str, default: Any = None) -> Any:
    """
    Get a nested configuration value using dot notation.
    
    Args:
        path: Configuration path (e.g., "database.host")
        default: Default value if not found
    
    Returns:
        Configuration value or default
    """
    parts = path.split(".")
    value = config
    
    for part in parts:
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    
    return value

def get_full_config() -> Dict[str, Any]:
    """
    Get the full configuration dictionary.
    
    Returns:
        Complete configuration dictionary
    """
    return config.copy()

def is_feature_enabled(feature_name: str) -> bool:
    """
    Check if a feature is enabled in configuration.
    
    Args:
        feature_name: Name of the feature to check
    
    Returns:
        True if the feature is enabled, False otherwise
    """
    return get_config_value("features", feature_name, False)

# Environment helper functions
def is_production() -> bool:
    """Check if running in production environment."""
    return ENVIRONMENT == "production"

def is_development() -> bool:
    """Check if running in development environment."""
    return ENVIRONMENT == "development"

def is_test() -> bool:
    """Check if running in test environment."""
    return ENVIRONMENT == "test"

def is_debug_enabled() -> bool:
    """Check if debug mode is enabled."""
    return DEBUG
