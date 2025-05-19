"""
Environment configuration for the Core Banking System
Provides environment detection and configuration for different deployment scenarios.
"""
import os
import sys
from enum import Enum
from typing import Dict, Any, Optional

class Environment(Enum):
    """Enum representing different deployment environments"""
    PRODUCTION = "production"
    DEVELOPMENT = "development" 
    TEST = "test"
    
    @classmethod
    def from_string(cls, value: str) -> "Environment":
        """Convert string to Environment enum value"""
        value = value.lower()
        if value == "production" or value == "prod":
            return cls.PRODUCTION
        elif value == "test" or value == "testing":
            return cls.TEST
        else:
            return cls.DEVELOPMENT  # Default to development

# Detect environment from environment variable
def get_environment() -> Environment:
    """Get the current environment as an Environment enum"""
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    return Environment.from_string(env_str)

# Environment name getter
def get_environment_name() -> str:
    """Get the current environment name as a string"""
    return get_environment().value.capitalize()

# Environment check functions
def is_production() -> bool:
    """Check if current environment is production"""
    return get_environment() == Environment.PRODUCTION

def is_development() -> bool:
    """Check if current environment is development"""
    return get_environment() == Environment.DEVELOPMENT

def is_test() -> bool:
    """Check if current environment is test"""
    return get_environment() == Environment.TEST

# Debug mode detection
def is_debug_enabled() -> bool:
    """Check if debug mode is enabled"""
    debug_env = os.environ.get("CBS_DEBUG", "false").lower()
    return debug_env in ("true", "1", "yes")

# Config loading
def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get configuration value from environment variables
    
    Args:
        key: The configuration key (will be converted to CBS_KEY format)
        default: Default value if not found
        
    Returns:
        Configuration value or default
    """
    env_key = f"CBS_{key.upper()}"
    return os.environ.get(env_key, default)

# Environment-specific configuration dictionary
def get_environment_config() -> Dict[str, Any]:
    """Get environment-specific configuration dictionary"""
    return {
        "name": get_environment_name(),
        "is_production": is_production(),
        "is_development": is_development(),
        "is_test": is_test(),
        "debug_enabled": is_debug_enabled(),
        "log_level": os.environ.get("CBS_LOG_LEVEL", "INFO")
    }
