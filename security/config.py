"""
Security Configuration for Core Banking System

IMPORTANT: This module now imports from the main config.py file.
This file is kept for backward compatibility.
All security configuration settings are now centralized in the root config.py.
"""

import sys
import os
import logging
from typing import Any, Optional, Dict, List

# Add the parent directory to sys.path to ensure we can import from the root

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed

# Add ENVIRONMENT variable with a default value for module usage
ENVIRONMENT = os.environ.get("CBS_ENVIRONMENT", "development")

# Try to import from main config
try:
    from config import SECURITY_CONFIG
except ImportError:
    # If main config is not available, use local defaults
    SECURITY_CONFIG = {}

# Configure logger
logger = logging.getLogger(__name__)

# Security configuration with defaults
DEFAULT_CONFIG = {
    "jwt_secret": os.environ.get("JWT_SECRET", "development_secret_key"),
    "jwt_algorithm": "HS256",
    "jwt_expiration": 3600,  # 1 hour in seconds
    "password_min_length": 10,
    "password_require_uppercase": True,
    "password_require_lowercase": True,
    "password_require_digits": True,
    "password_require_special": True,
    "password_max_age_days": 90,
    "max_login_attempts": 5,
    "lockout_duration_minutes": 30,
    "session_timeout_minutes": 30,
    "enable_mfa": False,
    "cors_origins": ["*"],
    "cors_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "cors_headers": ["Content-Type", "Authorization"],
    "enable_csp": True,
    "enable_xss_protection": True,
    "enable_rate_limiting": True,
}

# Merge with imported config, if any
CONFIG = {**DEFAULT_CONFIG, **SECURITY_CONFIG}

# Defining additional configuration variables for module usage
if 'JWT_CONFIG' not in globals():
    JWT_CONFIG = {
        "secret_key": os.environ.get("JWT_SECRET_KEY", "development-insecure-key"),
        "algorithm": "HS256",
        "access_token_expire_minutes": 30
    }

# CORS Configuration for API Gateway
CORS_CONFIG = {
    "allowed_origins": CONFIG.get("cors_origins", ["*"]),
    "allowed_methods": CONFIG.get("cors_methods", ["GET", "POST", "PUT", "DELETE", "OPTIONS"]),
    "allowed_headers": CONFIG.get("cors_headers", ["Content-Type", "Authorization"]),
    "expose_headers": CONFIG.get("cors_expose_headers", []),
    "supports_credentials": CONFIG.get("cors_supports_credentials", True),
    "max_age": CONFIG.get("cors_max_age", 3600)
}

# Multi-factor authentication settings
MFA_CONFIG = {
    "enabled": CONFIG.get("enable_mfa", False),
    "totp_issuer": CONFIG.get("totp_issuer", "CBS_Security"),
    "totp_digits": 6,
    "totp_interval": 30,  # seconds
    "backup_codes_count": 10,
}

# Rate limiting settings
RATE_LIMIT_CONFIG = {
    "default_limits": ["100 per hour", "5 per minute"],
    "login_limits": ["5 per minute", "20 per hour"],
    "sensitive_api_limits": ["3 per minute", "10 per hour"],
    "storage_uri": os.environ.get("RATE_LIMIT_STORAGE", "memory://"),
}

# Security headers
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
}

# Certificate settings
CERTIFICATE_CONFIG = {
    "cert_dir": "security/certificates/certs",
    "private_key_dir": "security/certificates/private",
    "csr_dir": "security/certificates/csr",
    "cert_validity_days": 365,
    "key_size": 4096,
    "signature_algorithm": "sha256",
    "min_tls_version": "TLSv1.2",
    "preferred_ciphers": (
        "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:"
        "ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305"
    ),
}

# Audit logging configuration
AUDIT_LOG_CONFIG = {
    "log_file_path": "logs/security_audit.log",
    "log_level": "INFO",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "sensitive_actions": [
        "login", "logout", "password_change", "fund_transfer", 
        "admin_access", "permission_change", "user_creation"
    ],
}

def get_config_value(config_path: str, default: Any = None) -> Any:
    """
    Get a configuration value using a dot-notation path
    
    Args:
        config_path: Dot-notation path to the config value (e.g., "jwt.expiration")
        default: Default value to return if the path is not found
        
    Returns:
        The configuration value or the default if not found
    """
    try:
        # Split the path into parts
        parts = config_path.split('.')
        
        # Start with the top-level config
        config = CONFIG
        
        # Navigate through the path
        for part in parts[:-1]:
            if part not in config:
                return default
            config = config[part]
        
        # Get the final value
        final_part = parts[-1]
        if final_part not in config:
            return default
        
        return config[final_part]
    except Exception as e:
        logger.error(f"Error getting config value for {config_path}: {str(e)}")
        return default


# Import everything from the main config file
# Comment this out to avoid import errors
# from config import *

# Keep the security-specific configs here for backward compatibility
# These variables are now imported from the main config

# Password policy settings
PASSWORD_POLICY = {
    "min_length": 10,
    "min_uppercase": 1,
    "min_lowercase": 1,
    "min_digits": 1,
    "min_special": 1,
    "special_chars": "!@#$%^&*()-_=+[]{}|;:,.<>?/",
    "history_size": 5,  # Number of previous passwords to remember
    "max_age_days": 90,  # Maximum password age before requiring change
    "lockout_threshold": 5,  # Failed attempts before account lockout
    "lockout_duration_minutes": 30,  # Duration of account lockout
}

# Encryption settings
ENCRYPTION_CONFIG = {
    "algorithm": "AES-256-CBC",
    "key_derivation": "PBKDF2",
    "pbkdf2_iterations": 600000,
    "key_length": 32,  # 256 bits
    "iv_length": 16,  # 128 bits
}

# Two-factor authentication settings
MFA_CONFIG = {
    "enabled": True,
    "totp_issuer": "CoreBankingSystem",
    "totp_digits": 6,
    "totp_interval": 30,  # seconds
    "backup_codes_count": 10,
}

# Rate limiting settings
RATE_LIMIT_CONFIG = {
    "default_limits": ["100 per hour", "5 per minute"],
    "login_limits": ["5 per minute", "20 per hour"],
    "sensitive_api_limits": ["3 per minute", "10 per hour"],
    "storage_uri": os.environ.get("RATE_LIMIT_STORAGE", "memory://"),
}

# Security headers
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
}

# Certificate settings
CERTIFICATE_CONFIG = {
    "cert_dir": "security/certificates/certs",
    "private_key_dir": "security/certificates/private",
    "csr_dir": "security/certificates/csr",
    "cert_validity_days": 365,
    "key_size": 4096,
    "signature_algorithm": "sha256",
    "min_tls_version": "TLSv1.2",
    "preferred_ciphers": (
        "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:"
        "ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305"
    ),
}

# Audit logging configuration
AUDIT_LOG_CONFIG = {
    "log_file_path": "logs/security_audit.log",
    "log_level": "INFO",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "sensitive_actions": [
        "login", "logout", "password_change", "fund_transfer", 
        "account_creation", "role_change", "permission_change"
    ],
}

# Security monitoring configuration
SECURITY_MONITORING = {
    "anomaly_detection_enabled": True,
    "alert_threshold": 0.85,  # Confidence level for anomaly alerts (0-1)
    "monitoring_interval_minutes": 5,
    "max_failed_logins_per_hour": 10,
    "max_transactions_per_hour": 100,  # For anomaly detection
    "ip_whitelist": [],  # Trusted IP addresses
    "ip_blacklist": [],  # Blocked IP addresses
}

# Secure session settings
SESSION_CONFIG = {
    "cookie_secure": True,
    "cookie_httponly": True,
    "cookie_samesite": "Strict",
    "session_timeout_minutes": 30,
    "session_lifetime_hours": 24,
    "regenerate_id_on_login": True,
}

# CORS configuration
CORS_CONFIG = {
    "allowed_origins": ["https://banking.example.com"],
    "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allowed_headers": ["Content-Type", "Authorization"],
    "expose_headers": ["Content-Length", "X-Request-Id"],
    "supports_credentials": True,
    "max_age": 600,  # Preflight cache time in seconds
}

# Environment-specific overrides
if ENVIRONMENT == "development":
    JWT_CONFIG["access_token_expire_minutes"] = 60 * 24  # 24 hours for development
    PASSWORD_POLICY["lockout_threshold"] = 10  # More lenient in development
    MFA_CONFIG["enabled"] = False  # Optional in development
    CORS_CONFIG["allowed_origins"] = ["*"]  # More permissive in development
    
elif ENVIRONMENT == "test":
    JWT_CONFIG["access_token_expire_minutes"] = 5  # Short-lived tokens for testing
    RATE_LIMIT_CONFIG["default_limits"] = ["1000 per hour"]  # More permissive for testing
    SECURITY_MONITORING["anomaly_detection_enabled"] = False
    
elif ENVIRONMENT == "production":
    # Ensure secure defaults for production
    if JWT_CONFIG["secret_key"] == "development-insecure-key":
        raise ValueError("Production environment requires a secure JWT_SECRET_KEY")
    
    # Force more secure settings in production
    PASSWORD_POLICY["min_length"] = 12
    SESSION_CONFIG["cookie_secure"] = True
    CERTIFICATE_CONFIG["min_tls_version"] = "TLSv1.3"


def get_config_value(config_name, key):
    """
    Safely get a configuration value with proper error handling
    
    Args:
        config_name (str): The name of the configuration dict
        key (str): The key to retrieve
        
    Returns:
        The configuration value if it exists
    
    Raises:
        KeyError: If the configuration or key doesn't exist
    """
    config_dict = globals().get(config_name)
    if config_dict is None:
        raise KeyError(f"Configuration '{config_name}' not found")
    
    if key not in config_dict:
        raise KeyError(f"Key '{key}' not found in configuration '{config_name}'")
    
    return config_dict[key]


def get_config_value(key: str, default=None):
    """
    Get a configuration value by key with optional default
    
    Args:
        key: Configuration key (dot notation for nested keys)
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    keys = key.split('.')
    config_dict = globals()
    
    try:
        value = config_dict
        for k in keys:
            if k.isdigit() and isinstance(value, list):
                value = value[int(k)]
            elif isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    except (KeyError, IndexError, TypeError):
        return default