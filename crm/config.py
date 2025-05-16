"""
CRM Configuration Module

This module contains configuration settings for the CRM system.
"""

import os

# Add parent directory to path if needed

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


# Try importing from main config
try:
    from config import DATABASE_CONFIG, CRM_CONFIG
    
    # Extract CRM specific configuration
    CRM_SETTINGS = CRM_CONFIG if 'CRM_CONFIG' in locals() else {}
    
except ImportError:
    # Default configuration
    CRM_SETTINGS = {
        'campaign_cool_off_days': 30,
        'lead_follow_up_days': 7,
        'customer_engagement_frequency': 90,
        'notification_channels': ['email', 'sms', 'app_notification']
    }
    
    DATABASE_CONFIG = {
        'host': 'localhost',
        'database': 'CBS_PYTHON',
        'user': 'root',
        'password': '',
        'port': 3307,
    }

# Campaign management settings
CAMPAIGN_SETTINGS = {
    'max_simultaneous_campaigns': 5,
    'min_target_audience': 100,
    'default_duration_days': 30
}

# Lead management settings
LEAD_SETTINGS = {
    'lead_expiry_days': 60,
    'auto_assign': True,
    'scoring_threshold': 60
}

# Customer 360 settings
CUSTOMER_360_SETTINGS = {
    'data_sources': ['core_banking', 'transactions', 'payments', 'digital_channels'],
    'refresh_frequency_hours': 24,
    'cache_enabled': True
}