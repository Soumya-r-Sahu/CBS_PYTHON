"""
Compatibility Layer for Import Migration

This module provides backwards compatibility while preparing for an eventual migration 
to a standardized structure. Note: The CBS package structure implementation has been 
rolled back as of May 15, 2025. This file is retained for future migration plans.

It also provides cross-framework compatibility configuration to ensure the banking system
API works seamlessly with various frontend frameworks including Django, React, Angular, 
and Vue.js.
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

def get_cors_settings() -> Dict[str, Any]:
    """
    Get CORS configuration settings optimized for cross-framework compatibility
    
    Returns:
        Dictionary with CORS configuration settings
    """
    cors_config = {
        # Use allowed origins from API config
        "allowed_origins": get_api_config().get("allowed_origins", ["*"]),
        
        # Standard HTTP methods needed for REST API
        "allowed_methods": [
            "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"
        ],
        
        # Headers needed for modern frontend frameworks
        "allowed_headers": [
            "Authorization", "Content-Type", "Accept", 
            "Origin", "X-Requested-With", "X-CSRF-Token",
            "X-CSRFToken", "X-Django-CSRF-Token", "Cache-Control",
            "X-Auth-Token", "X-Requested-By"
        ],
        
        # Headers to expose to the frontend application
        "expose_headers": [
            "Content-Disposition", "X-Pagination", "X-Rate-Limit",
            "X-Rate-Limit-Remaining"
        ],
        
        # Enable credentials for authenticated requests
        "supports_credentials": True,
        
        # Cache preflight request results for 1 hour (3600 seconds)
        "max_age": 3600
    }
    
    # Get origin overrides from environment
    if os.environ.get("CBS_CORS_ALLOWED_ORIGINS"):
        cors_config["allowed_origins"] = os.environ.get("CBS_CORS_ALLOWED_ORIGINS").split(",")
    
    # Check for development-specific settings
    if not is_production():
        # Always include localhost domains for local development
        dev_origins = [
            "http://localhost:8000",  # Django default
            "http://127.0.0.1:8000",
            "http://localhost:3000",  # React/Next.js default
            "http://localhost:4200",  # Angular default
            "http://localhost:8080",  # Vue.js default
            "http://127.0.0.1:3000",
            "http://127.0.0.1:4200",
            "http://127.0.0.1:8080"
        ]
        
        # Add development origins if not using wildcard
        if "*" not in cors_config["allowed_origins"]:
            cors_config["allowed_origins"].extend(dev_origins)
    
    return cors_config

def get_api_client_config(framework: str = "django") -> Dict[str, Any]:
    """
    Get configuration settings for API client libraries
    
    Args:
        framework: The frontend framework name (django, react, angular, vue, etc.)
    
    Returns:
        Dictionary with API client configuration
    """
    api_config = get_api_config()
    api_host = api_config.get("host", "0.0.0.0")
    api_port = api_config.get("port", 5000)
    
    # Base config that works for all frameworks
    client_config = {
        "base_url": f"http://{api_host}:{api_port}/api/v1",
        "timeout": 30000,  # Default timeout in milliseconds (30 seconds)
        "retry_attempts": 3,
        "content_type": "application/json",
        "credentials": "include",  # Include credentials in requests
        "token_storage_key": "jwt_token",  # Default token storage key
        "cache_control": "no-cache",  # Default cache control header
        "default_headers": {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    }
    
    # Production settings
    if is_production():
        client_config["base_url"] = get_config_value(
            "API_URL", 
            "https://api.bank.example.com/api/v1"
        )
        # Add production-specific security headers
        client_config["default_headers"].update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        })
    
    # Override with environment variable if provided
    if os.environ.get("CBS_API_BASE_URL"):
        client_config["base_url"] = os.environ.get("CBS_API_BASE_URL")
    
    # Framework-specific customizations
    if framework.lower() == "django":
        client_config.update({
            "csrf_header": "X-CSRFToken",
            "csrf_cookie_name": "csrftoken",
            "session_cookie_name": "sessionid",
            "token_type": "JWT",
            "authentication_scheme": "Bearer"
        })
    elif framework.lower() in ["react", "nextjs"]:
        client_config.update({
            "use_fetch": True,
            "request_library": "fetch",
            "token_type": "JWT",
            "authentication_scheme": "Bearer",
            "extra_headers": {
                "X-Requested-With": "XMLHttpRequest"
            },
            "response_type": "json"
        })
    elif framework.lower() == "angular":
        client_config.update({
            "use_http_client": True,
            "request_library": "HttpClient",
            "interceptors_enabled": True,
            "token_type": "JWT",
            "authentication_scheme": "Bearer",
            "enable_rxjs": True,
            "add_credentials": True,
            "response_type": "json",
            "extra_headers": {
                "X-Requested-With": "XMLHttpRequest"
            }
        })
    elif framework.lower() == "vue":
        client_config.update({
            "use_axios": True,
            "request_library": "axios",
            "token_type": "JWT",
            "authentication_scheme": "Bearer",
            "enable_composables": True,
            "response_type": "json",
            "extra_headers": {
                "X-Requested-With": "XMLHttpRequest"
            }
        })
    
    return client_config

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

def detect_framework_from_request(user_agent: str = None, headers: Dict[str, str] = None) -> str:
    """
    Detect the frontend framework from request headers or user agent
    
    Args:
        user_agent: The User-Agent header from the request
        headers: Dictionary of request headers
    
    Returns:
        Framework name string (django, react, angular, vue, or generic)
    """
    if headers is None:
        headers = {}
    
    # Default to generic if no info provided
    if not user_agent and not headers:
        return "generic"
    
    user_agent = user_agent or headers.get("User-Agent", "")
    
    # Check for framework-specific patterns in headers
    if headers.get("X-Django-CSRF-Token") or headers.get("X-CSRFToken"):
        return "django"
    
    if headers.get("X-Requested-By") == "Angular":
        return "angular"
    
    if headers.get("X-Requested-With") == "XMLHttpRequest":
        # Need more info to distinguish between React and Vue.js
        if "react" in user_agent.lower():
            return "react"
        elif "vue" in user_agent.lower():
            return "vue"
    
    # Check user agent for framework clues
    if "angular" in user_agent.lower():
        return "angular"
    elif "react" in user_agent.lower():
        return "react"
    elif "vue" in user_agent.lower():
        return "vue"
    elif "django" in user_agent.lower():
        return "django"
    
    # Default to generic if no match
    return "generic"

def get_authentication_scheme(framework: str = "generic") -> str:
    """
    Get the appropriate authentication scheme for the specified framework
    
    Args:
        framework: Frontend framework name
    
    Returns:
        Authentication scheme string (e.g., 'Bearer', 'JWT', 'Token')
    """
    # All modern frameworks use Bearer token auth by default
    return "Bearer"
