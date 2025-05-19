"""
API Configuration for the CBS_PYTHON system.

This module provides access to API configuration settings.
"""

import os
import sys
from pathlib import Path

# Use centralized import system
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from utils.config.environment import (
        get_environment,
        is_production,
        is_development,
        is_debug_enabled
    )
except ImportError:
    # Define fallbacks if the environment module isn't available
    def get_environment(): return "development"
    def is_production(): return False
    def is_development(): return True
    def is_debug_enabled(): return True

def get_api_config():
    """
    Get API configuration settings
    
    Returns:
        Dictionary with API configuration
    """
    # Base configuration
    config = {
        "host": "0.0.0.0",
        "port": int(os.environ.get("CBS_API_PORT", 5000)),
        "debug": is_debug_enabled(),
        "workers": int(os.environ.get("CBS_API_WORKERS", 4)),
        "timeout": int(os.environ.get("CBS_API_TIMEOUT", 30)),
        "rate_limit": int(os.environ.get("CBS_API_RATE_LIMIT", 100)),
        "secret_key": os.environ.get("CBS_API_SECRET_KEY", "dev-secret-key-change-me"),
    }
    
    # Environment-specific settings
    if is_production():
        config.update({
            "debug": False,
            "allowed_origins": [
                "https://bank.example.com",
                "https://admin.bank.example.com"
            ],
            "rate_limit": 300,
            "workers": 8,
            "log_level": "INFO"
        })
    else:
        config.update({
            "allowed_origins": ["*"],  # Allow all origins in non-production
            "log_level": "DEBUG" if is_debug_enabled() else "INFO"
        })
    
    # Override with environment variables if provided
    if os.environ.get("CBS_API_ALLOWED_ORIGINS"):
        config["allowed_origins"] = os.environ.get("CBS_API_ALLOWED_ORIGINS").split(",")
    
    if os.environ.get("CBS_API_LOG_LEVEL"):
        config["log_level"] = os.environ.get("CBS_API_LOG_LEVEL")
    
    return config

def get_api_url(path=""):
    """
    Get the full URL for an API endpoint
    
    Args:
        path: API path to append to the base URL
        
    Returns:
        Full URL string
    """
    config = get_api_config()
    base_url = f"http://{config['host']}:{config['port']}"
    
    if is_production():
        # In production, we might use a different domain
        base_url = os.environ.get("CBS_API_URL", "https://api.bank.example.com")
    
    # Clean up the path and ensure it starts with /
    if path and not path.startswith("/"):
        path = f"/{path}"
    
    return f"{base_url}{path}"
