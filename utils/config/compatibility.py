"""
Compatibility Layer for Import Migration

This module provides backwards compatibility while preparing for an eventual migration 
to a standardized structure. Note: The CBS package structure implementation has been 
rolled back as of May 15, 2025. This file is retained for future migration plans.

IMPORTANT: Currently this module should be used only for environment configuration.
Other compatibility functionality will be added after revised planning.
"""

import warnings
import os
import sys
from typing import Any, Dict, Callable

# Environment constants for reference
ENVIRONMENT_PRODUCTION = "production"
ENVIRONMENT_DEVELOPMENT = "development"
ENVIRONMENT_TESTING = "testing"
ENVIRONMENT_TEST = "test"  # Legacy name
ENVIRONMENT_STAGING = "staging"

# Environment functions
env_str = os.environ.get("CBS_ENVIRONMENT", ENVIRONMENT_DEVELOPMENT).lower()

def get_environment() -> str:
    """Get the current environment name."""
    return env_str

def get_environment_name() -> str:
    """Legacy function to get environment name."""
    return env_str

def is_production() -> bool:
    """Check if current environment is production."""
    return env_str == ENVIRONMENT_PRODUCTION

def is_development() -> bool:
    """Check if current environment is development."""
    return env_str == ENVIRONMENT_DEVELOPMENT

def is_testing() -> bool:
    """Check if current environment is testing."""
    return env_str == ENVIRONMENT_TESTING

def is_test() -> bool:
    """Legacy function to check if environment is test."""
    return env_str == ENVIRONMENT_TEST or env_str == ENVIRONMENT_TESTING

def is_staging() -> bool:
    """Check if current environment is staging."""
    return env_str == ENVIRONMENT_STAGING

def is_debug_enabled() -> bool:
    """Check if debug mode is enabled."""
    default = "true" if is_development() else "false"
    return os.environ.get("CBS_DEBUG", default).lower() in ("true", "1", "yes")

def get_log_level() -> str:
    """Get the appropriate log level based on environment."""
    if is_debug_enabled():
        return "DEBUG"
    elif is_production():
        return "WARNING"
    else:
        return "INFO"

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value from environment variables."""
    env_key = f"CBS_{key.upper()}"
    return os.environ.get(env_key, default)

def get_database_config() -> Dict[str, str]:
    """Get database configuration from environment variables."""
    return {
        "host": get_config_value("DB_HOST", "localhost"),
        "port": get_config_value("DB_PORT", "3306"),
        "user": get_config_value("DB_USER", "root"),
        "password": get_config_value("DB_PASSWORD", ""),
        "database": get_config_value("DB_NAME", "cbs_python"),
    }

def get_api_config() -> Dict[str, Any]:
    """Get API configuration from environment variables."""
    return {
        "host": get_config_value("API_HOST", "0.0.0.0"),
        "port": int(get_config_value("API_PORT", "5000")),
        "debug": is_debug_enabled(),
        "secret_key": get_config_value("API_SECRET_KEY", "development-secret-key"),
        "allowed_origins": get_config_value("API_ALLOWED_ORIGINS", "*").split(","),
        "rate_limit": int(get_config_value("API_RATE_LIMIT", "100")),
    }

# The following section is for future implementation when the cbs/ structure is reimplemented
# Commented out for now
"""
# Add more compatibility imports here as modules are migrated to the new structure
# Example:
# try:
#     from cbs.core.accounts import AccountManager
# except ImportError:
#     from core_banking.accounts import AccountManager
"""
