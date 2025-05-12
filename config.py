"""
Core Banking System - Master Configuration

This is the central configuration file for the Core Banking System.
All credentials and configuration settings should be accessed from here.
Other modules should import their configuration from this file.

Production environments should use environment variables instead of hard-coded values.
"""

import os
import logging
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Environment-specific configuration
ENVIRONMENT = os.environ.get("CBS_ENVIRONMENT", "development")
DEBUG_MODE = ENVIRONMENT != "production"

# ======================================================================
# DATABASE CONFIGURATION
# ======================================================================
DATABASE_CONFIG = {
    'host': os.environ.get('CBS_DB_HOST', 'localhost'),
    'database': os.environ.get('CBS_DB_NAME', 'CBS_PYTHON'),
    'user': os.environ.get('CBS_DB_USER', 'root'),
    'password': os.environ.get('CBS_DB_PASSWORD', ''),
    'port': int(os.environ.get('CBS_DB_PORT', 3307)),
    'pool_size': int(os.environ.get('CBS_DB_POOL_SIZE', 5)),
    'max_overflow': int(os.environ.get('CBS_DB_MAX_OVERFLOW', 10)),
    'timeout': int(os.environ.get('CBS_DB_TIMEOUT', 30)),
}

# Legacy database URL format (keeping for reference and backward compatibility)
DATABASE_URL = os.environ.get('CBS_DATABASE_URL', "sqlite:///database/cbs.db") 

# ======================================================================
# SECURITY CONFIGURATION
# ======================================================================
# Core security settings
SECRET_KEY = os.environ.get('CBS_SECRET_KEY', "development-insecure-key")
ALLOWED_HOSTS = os.environ.get('CBS_ALLOWED_HOSTS', "localhost,127.0.0.1").split(',')

# JWT Authentication settings
JWT_CONFIG = {
    "secret_key": os.environ.get("CBS_JWT_SECRET_KEY", SECRET_KEY),
    "algorithm": "HS256",
    "access_token_expire_minutes": int(os.environ.get('CBS_JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 30)),
    "refresh_token_expire_days": int(os.environ.get('CBS_JWT_REFRESH_TOKEN_EXPIRE_DAYS', 7)),
}

# Password policy settings
PASSWORD_POLICY = {
    "min_length": int(os.environ.get('CBS_PASSWORD_MIN_LENGTH', 10)),
    "min_uppercase": int(os.environ.get('CBS_PASSWORD_MIN_UPPERCASE', 1)),
    "min_lowercase": int(os.environ.get('CBS_PASSWORD_MIN_LOWERCASE', 1)),
    "min_digits": int(os.environ.get('CBS_PASSWORD_MIN_DIGITS', 1)),
    "min_special": int(os.environ.get('CBS_PASSWORD_MIN_SPECIAL', 1)),
    "special_chars": os.environ.get('CBS_PASSWORD_SPECIAL_CHARS', "!@#$%^&*()-_=+[]{}|;:,.<>?/"),
    "history_size": int(os.environ.get('CBS_PASSWORD_HISTORY_SIZE', 5)),
    "max_age_days": int(os.environ.get('CBS_PASSWORD_MAX_AGE_DAYS', 90)),
    "lockout_threshold": int(os.environ.get('CBS_PASSWORD_LOCKOUT_THRESHOLD', 5)),
    "lockout_duration_minutes": int(os.environ.get('CBS_PASSWORD_LOCKOUT_DURATION', 30)),
}

# Encryption settings
ENCRYPTION_CONFIG = {
    "algorithm": os.environ.get('CBS_ENCRYPTION_ALGORITHM', "AES-256-CBC"),
    "key_derivation": os.environ.get('CBS_ENCRYPTION_KEY_DERIVATION', "PBKDF2"),
    "pbkdf2_iterations": int(os.environ.get('CBS_ENCRYPTION_PBKDF2_ITERATIONS', 600000)),
    "key_length": int(os.environ.get('CBS_ENCRYPTION_KEY_LENGTH', 32)),  # 256 bits
    "iv_length": int(os.environ.get('CBS_ENCRYPTION_IV_LENGTH', 16)),    # 128 bits
}

# Two-factor authentication settings
MFA_CONFIG = {
    "enabled": os.environ.get('CBS_MFA_ENABLED', 'true').lower() == 'true',
    "totp_issuer": os.environ.get('CBS_MFA_TOTP_ISSUER', "CoreBankingSystem"),
    "totp_digits": int(os.environ.get('CBS_MFA_TOTP_DIGITS', 6)),
    "totp_interval": int(os.environ.get('CBS_MFA_TOTP_INTERVAL', 30)),  # seconds
    "backup_codes_count": int(os.environ.get('CBS_MFA_BACKUP_CODES_COUNT', 10)),
}

# Rate limiting settings
RATE_LIMIT_CONFIG = {
    "default_limits": os.environ.get('CBS_RATE_DEFAULT_LIMITS', "100 per hour,5 per minute").split(','),
    "login_limits": os.environ.get('CBS_RATE_LOGIN_LIMITS', "5 per minute,20 per hour").split(','),
    "sensitive_api_limits": os.environ.get('CBS_RATE_SENSITIVE_API_LIMITS', "3 per minute,10 per hour").split(','),
    "storage_uri": os.environ.get("CBS_RATE_STORAGE", "memory://"),
}

# Security headers
SECURITY_HEADERS = {
    "Strict-Transport-Security": os.environ.get('CBS_HEADER_HSTS', "max-age=31536000; includeSubDomains"),
    "X-Content-Type-Options": os.environ.get('CBS_HEADER_CONTENT_TYPE', "nosniff"),
    "X-Frame-Options": os.environ.get('CBS_HEADER_FRAME_OPTIONS', "DENY"),
    "X-XSS-Protection": os.environ.get('CBS_HEADER_XSS_PROTECTION', "1; mode=block"),
    "Content-Security-Policy": os.environ.get('CBS_HEADER_CSP', "default-src 'self'; script-src 'self'; object-src 'none'"),
    "Referrer-Policy": os.environ.get('CBS_HEADER_REFERRER', "strict-origin-when-cross-origin"),
    "Permissions-Policy": os.environ.get('CBS_HEADER_PERMISSIONS', "geolocation=(), camera=(), microphone=()"),
}

# Certificate settings
CERTIFICATE_CONFIG = {
    "cert_dir": os.environ.get('CBS_CERT_DIR', "security/certificates/certs"),
    "private_key_dir": os.environ.get('CBS_PRIVATE_KEY_DIR', "security/certificates/private"),
    "csr_dir": os.environ.get('CBS_CSR_DIR', "security/certificates/csr"),
    "cert_validity_days": int(os.environ.get('CBS_CERT_VALIDITY_DAYS', 365)),
    "key_size": int(os.environ.get('CBS_KEY_SIZE', 4096)),
    "signature_algorithm": os.environ.get('CBS_SIGNATURE_ALGORITHM', "sha256"),
    "min_tls_version": os.environ.get('CBS_MIN_TLS_VERSION', "TLSv1.2"),
    "preferred_ciphers": os.environ.get('CBS_CIPHERS', (
        "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:"
        "ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305"
    )),
}

# ======================================================================
# LOGGING CONFIGURATION
# ======================================================================
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.environ.get('CBS_LOG_FILE', "logs/cbs.log"),
            "formatter": "simple",
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"] if ENVIRONMENT == "production" else ["console"],
            "level": os.environ.get('CBS_LOG_LEVEL', "INFO" if ENVIRONMENT == "production" else "DEBUG"),
        },
    },
}

# Audit logging configuration
AUDIT_LOG_CONFIG = {
    "log_file_path": os.environ.get('CBS_AUDIT_LOG_FILE', "logs/security_audit.log"),
    "log_level": os.environ.get('CBS_AUDIT_LOG_LEVEL', "INFO"),
    "log_format": os.environ.get('CBS_AUDIT_LOG_FORMAT', "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    "sensitive_actions": os.environ.get('CBS_AUDIT_SENSITIVE_ACTIONS', 
                                        "login,logout,password_change,fund_transfer,"
                                        "account_creation,role_change,permission_change").split(','),
}

# ======================================================================
# EMAIL CONFIGURATION
# ======================================================================
EMAIL_CONFIG = {
    "host": os.environ.get('CBS_EMAIL_HOST', "smtp.example.com"),
    "port": int(os.environ.get('CBS_EMAIL_PORT', 587)),
    "user": os.environ.get('CBS_EMAIL_USER', "your_email@example.com"),
    "password": os.environ.get('CBS_EMAIL_PASSWORD', ""),
    "use_tls": os.environ.get('CBS_EMAIL_USE_TLS', 'true').lower() == 'true',
    "use_ssl": os.environ.get('CBS_EMAIL_USE_SSL', 'false').lower() == 'true',
    "default_sender": os.environ.get('CBS_EMAIL_DEFAULT_SENDER', "Core Banking System <noreply@example.com>"),
}

# ======================================================================
# UPI CONFIGURATION
# ======================================================================
UPI_CONFIG = {
    "provider": os.environ.get('CBS_UPI_PROVIDER', ""),
    "api_key": os.environ.get('CBS_UPI_API_KEY', ""),
    "api_url": os.environ.get('CBS_UPI_API_URL', "https://api.upi.example.com/v1/"),
    "timeout": int(os.environ.get('CBS_UPI_TIMEOUT', 30)),
    "verify_ssl": os.environ.get('CBS_UPI_VERIFY_SSL', 'true').lower() == 'true',
}

# ======================================================================
# ATM CONFIGURATION
# ======================================================================
ATM_CONFIG = {
    "max_withdrawal_limit": int(os.environ.get('CBS_ATM_MAX_WITHDRAWAL', 10000)),
    "pin_attempts": int(os.environ.get('CBS_ATM_PIN_ATTEMPTS', 3)),
    "session_timeout_seconds": int(os.environ.get('CBS_ATM_SESSION_TIMEOUT', 120)),
}

# ======================================================================
# SERVICE URLS AND ENDPOINTS
# ======================================================================
SERVICE_URLS = {
    "api_gateway": os.environ.get('CBS_API_GATEWAY_URL', "http://localhost:8000"),
    "admin_panel": os.environ.get('CBS_ADMIN_PANEL_URL', "http://localhost:8080"),
    "mobile_api": os.environ.get('CBS_MOBILE_API_URL', "http://localhost:8001"),
}

# Initialize logging with the defined configuration
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Log a message on successful config loading
if DEBUG_MODE:
    logger.debug("Configuration loaded successfully in DEBUG mode")
    if env_path.exists():
        logger.debug(f"Environment variables loaded from {env_path}")
    else:
        logger.warning(f"No .env file found at {env_path}, using default values")
else:
    logger.info("Configuration loaded successfully")
