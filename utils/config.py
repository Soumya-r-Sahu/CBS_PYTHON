"""
Core Banking System - Centralized Configuration Module

This module serves as a centralized configuration interface for the Core Banking System.
It imports settings from the main config.py file and provides backward compatibility
for components that still reference the old configuration paths.

IMPORTANT: This is a compatibility layer. For new code, import directly from the
root config.py file instead.

Usage:
    from utils.config import DATABASE_CONFIG, API_CONFIG
    
    # Access configuration settings
    db_host = DATABASE_CONFIG['host']
    api_port = API_CONFIG['port']
"""

import sys
from pathlib import Path

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Add project root to path

# Import everything from the main config file
try:
    from config import *
except ImportError:
    # Fallback if main config cannot be imported
    import os
    import json
    import logging
    
    # Setup minimal logging
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger(__name__)
    logger.warning("Main config.py could not be imported. Using fallback configuration.")
    
    # Define minimal configuration
    DATABASE_CONFIG = {
        'host': os.environ.get('CBS_DB_HOST', 'localhost'),
        'port': int(os.environ.get('CBS_DB_PORT', '3306')),
        'user': os.environ.get('CBS_DB_USER', 'root'),
        'password': os.environ.get('CBS_DB_PASSWORD', ''),
        'database': os.environ.get('CBS_DB_NAME', 'cbs_python')
    }
    
    API_CONFIG = {
        'host': os.environ.get('CBS_API_HOST', '0.0.0.0'),
        'port': int(os.environ.get('CBS_API_PORT', '5000')),
        'debug': os.environ.get('CBS_DEBUG', 'true').lower() in ('true', '1', 'yes')
    }
    
    # Payment service configurations
    UPI_CONFIG = {
        'provider': os.environ.get('CBS_UPI_PROVIDER', 'default'),
        'enabled': os.environ.get('CBS_UPI_ENABLED', 'true').lower() in ('true', '1', 'yes')
    }

# Maintain backward compatibility with any code that uses these specific variable names
# These are now imported from the main config but are kept here for reference
try:
    UPI_PROVIDER = UPI_CONFIG["provider"]
except (NameError, KeyError):
    UPI_PROVIDER = "default"
UPI_API_KEY = UPI_CONFIG["api_key"]
ATM_MAX_WITHDRAWAL_LIMIT = ATM_CONFIG["max_withdrawal_limit"]
ATM_PIN_ATTEMPTS = ATM_CONFIG["pin_attempts"]
EMAIL_HOST = EMAIL_CONFIG["host"]
EMAIL_PORT = EMAIL_CONFIG["port"]
EMAIL_HOST_USER = EMAIL_CONFIG["user"]
EMAIL_HOST_PASSWORD = EMAIL_CONFIG["password"]