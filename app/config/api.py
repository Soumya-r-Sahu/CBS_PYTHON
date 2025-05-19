"""
API configuration for the Core Banking System
Defines API endpoints, versions, and authentication settings.
"""
import os
from typing import Dict, Any, List

# Default API configuration
DEFAULT_API_CONFIG = {
    "version": "1.0.0",
    "base_path": "/api",
    "auth_required": True,
    "rate_limit": 100,  # requests per minute
    "timeout": 30,      # seconds
    "cors_enabled": True,
    "allowed_origins": ["*"],
    "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allowed_headers": ["Content-Type", "Authorization"],
    "max_content_length": 16 * 1024 * 1024,  # 16MB
}

# API version information
API_VERSIONS = {
    "v1": {
        "status": "stable",
        "deprecated": False,
        "sunset_date": None
    },
    "v2": {
        "status": "beta",
        "deprecated": False,
        "sunset_date": None
    }
}

def get_api_config() -> Dict[str, Any]:
    """
    Get the API configuration, with environment variable overrides
    
    Returns:
        Dictionary with API configuration
    """
    config = DEFAULT_API_CONFIG.copy()
    
    # Override with environment variables if present
    env_overrides = {
        "version": os.environ.get("CBS_API_VERSION"),
        "base_path": os.environ.get("CBS_API_BASE_PATH"),
        "auth_required": os.environ.get("CBS_API_AUTH_REQUIRED"),
        "rate_limit": os.environ.get("CBS_API_RATE_LIMIT"),
        "timeout": os.environ.get("CBS_API_TIMEOUT"),
        "cors_enabled": os.environ.get("CBS_API_CORS_ENABLED"),
        "max_content_length": os.environ.get("CBS_API_MAX_CONTENT_LENGTH"),
    }
    
    # Apply overrides if they exist
    for key, value in env_overrides.items():
        if value is not None:
            # Convert boolean strings
            if value.lower() in ("true", "yes", "1"):
                config[key] = True
            elif value.lower() in ("false", "no", "0"):
                config[key] = False
            # Convert numeric strings
            elif value.isdigit():
                config[key] = int(value)
            else:
                config[key] = value
    
    return config

def get_cors_settings() -> Dict[str, Any]:
    """
    Get CORS settings for the API
    
    Returns:
        Dictionary with CORS settings
    """
    api_config = get_api_config()
    
    # Get allowed origins from environment or default
    origins_env = os.environ.get("CBS_API_ALLOWED_ORIGINS")
    if origins_env:
        allowed_origins = origins_env.split(",")
    else:
        allowed_origins = api_config["allowed_origins"]
    
    return {
        "origins": allowed_origins,
        "methods": api_config["allowed_methods"],
        "allow_headers": api_config["allowed_headers"],
        "expose_headers": ["Content-Length", "X-API-Version"],
        "supports_credentials": True,
        "max_age": 86400  # 24 hours
    }

def is_api_versioned() -> bool:
    """
    Check if API versioning is enabled
    
    Returns:
        True if API versioning is enabled
    """
    return os.environ.get("CBS_API_VERSIONING", "true").lower() in ("true", "yes", "1")
