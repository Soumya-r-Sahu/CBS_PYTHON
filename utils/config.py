"""
Core Banking System - Utility Configuration

IMPORTANT: This module now imports from the main config.py file.
This file is kept for backward compatibility.
Direct all new imports to the root config.py file.
"""

import sys

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


# Import everything from the main config file
from config import *

# Maintain backward compatibility with any code that uses these specific variable names
# These are now imported from the main config but are kept here for reference

# Specific values that might have been referenced directly
UPI_PROVIDER = UPI_CONFIG["provider"]
UPI_API_KEY = UPI_CONFIG["api_key"]
ATM_MAX_WITHDRAWAL_LIMIT = ATM_CONFIG["max_withdrawal_limit"]
ATM_PIN_ATTEMPTS = ATM_CONFIG["pin_attempts"]
EMAIL_HOST = EMAIL_CONFIG["host"]
EMAIL_PORT = EMAIL_CONFIG["port"]
EMAIL_HOST_USER = EMAIL_CONFIG["user"]
EMAIL_HOST_PASSWORD = EMAIL_CONFIG["password"]