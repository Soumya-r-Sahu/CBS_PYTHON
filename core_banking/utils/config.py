"""
Core Banking System Configuration Module

This module provides centralized configuration settings specifically for the 
Core Banking subsystem. It includes database connection parameters, environment 
detection, transaction limits, and notification settings.

Usage:
    from core_banking.utils.config import DATABASE_CONFIG, TRANSACTION_LIMITS
    from core_banking.utils.config import is_production, get_environment_name
    
    # Get database configuration
    db_config = get_database_config()
    
    # Check environment
    if is_production():
        # Apply production-specific logic
    
    # Get transaction limits for current environment
    limits = TRANSACTION_LIMITS[ENVIRONMENT]
    max_transfer = limits['single_transfer']
"""

import os
import sys
from pathlib import Path

# Add project root to path if needed
try:
    from utils.lib.packages import fix_path
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

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
    """
    Check if running in development environment
    
    Returns:
        bool: True if running in development environment
    """
    return ENVIRONMENT == 'development'

def is_test():
    """
    Check if running in test environment
    
    Returns:
        bool: True if running in test environment
    """
    return ENVIRONMENT == 'test'

def is_production():
    """
    Check if running in production environment
    
    Returns:
        bool: True if running in production environment
    """
    return ENVIRONMENT == 'production'

def get_environment_name():
    """
    Get current environment name with proper capitalization
    
    Returns:
        str: Capitalized environment name (Development, Test, Production)
    """
    return ENVIRONMENT.capitalize()

def get_database_config():
    """
    Return the current database configuration
    
    Returns:
        dict: Database connection parameters
    """
    return DATABASE_CONFIG

def get_table_prefix():
    """
    Get database table prefix for current environment
    
    In non-production environments, tables are prefixed with the
    environment name to prevent collisions (e.g., dev_accounts).
    
    Returns:
        str: Table prefix for current environment (empty in production)
    """
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
