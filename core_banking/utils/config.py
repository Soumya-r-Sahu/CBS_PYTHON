"""
Configuration module for Core Banking System utilities.
"""

import os
from pathlib import Path

# Database configuration with defaults
DATABASE_CONFIG = {
    'user': os.environ.get('CBS_DB_USER', 'root'),
    'password': os.environ.get('CBS_DB_PASSWORD', 'password'),
    'host': os.environ.get('CBS_DB_HOST', 'localhost'),
    'port': int(os.environ.get('CBS_DB_PORT', '3306')),
    'database': os.environ.get('CBS_DB_NAME', 'core_banking')
}

# Environment settings
ENVIRONMENT = os.environ.get('CBS_ENVIRONMENT', 'development').lower()
DEBUG = os.environ.get('CBS_DEBUG', 'true').lower() in ('true', '1', 'yes')

# Path settings
ROOT_PATH = Path(__file__).parent.parent.parent
LOGS_PATH = ROOT_PATH / 'logs'
BACKUPS_PATH = ROOT_PATH / 'backups'

# Helper functions for environment
def get_environment_name():
    """Return the current environment name with proper capitalization"""
    return ENVIRONMENT.capitalize()

def get_database_config():
    """Return the current database configuration"""
    return DATABASE_CONFIG

# Transaction limits by environment
TRANSACTION_LIMITS = {
    'development': {
        'single_transfer': 10000.00,
        'daily_total': 50000.00,
        'monthly_total': 200000.00
    },
    'test': {
        'single_transfer': 100000.00,
        'daily_total': 500000.00,
        'monthly_total': 2000000.00
    },
    'production': {
        'single_transfer': 1000000.00,
        'daily_total': 5000000.00,
        'monthly_total': 20000000.00
    }
}

# Environment helper functions
def is_development():
    """Check if running in development environment"""
    return ENVIRONMENT == 'development'

def is_test():
    """Check if running in test environment"""
    return ENVIRONMENT == 'test'

def is_production():
    """Check if running in production environment"""
    return ENVIRONMENT == 'production'

def get_environment_name():
    """Get current environment name with proper capitalization"""
    return ENVIRONMENT.capitalize()

def get_table_prefix():
    """Get database table prefix for current environment"""
    if is_production():
        return ""  # No prefix in production
    return f"{ENVIRONMENT}_"

# Notification settings
NOTIFICATION_CONFIG = {
    'email': {
        'enabled': os.environ.get('CBS_NOTIFY_EMAIL', 'true').lower() in ('true', '1', 'yes'),
        'server': os.environ.get('CBS_SMTP_SERVER', 'smtp.example.com'),
        'port': int(os.environ.get('CBS_SMTP_PORT', '587')),
        'user': os.environ.get('CBS_SMTP_USER', 'user@example.com'),
        'password': os.environ.get('CBS_SMTP_PASSWORD', 'password'),
        'use_tls': os.environ.get('CBS_SMTP_TLS', 'true').lower() in ('true', '1', 'yes')
    },
    'sms': {
        'enabled': os.environ.get('CBS_NOTIFY_SMS', 'false').lower() in ('true', '1', 'yes'),
        'provider': os.environ.get('CBS_SMS_PROVIDER', 'twilio'),
        'api_key': os.environ.get('CBS_SMS_API_KEY', ''),
        'sender_id': os.environ.get('CBS_SMS_SENDER', 'CBS')
    }
}
