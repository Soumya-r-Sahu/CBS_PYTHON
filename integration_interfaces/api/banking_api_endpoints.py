"""
Banking API Endpoints

This module organizes all the digital banking services into a structured API.
It provides a comprehensive set of endpoints for:

• Customer authentication and security
• Account management and balance checking
• Money transfers and payments
• Card management and controls
• Customer profile and preferences
• UPI and instant payment services

The API follows RESTful principles with proper versioning and error handling.
"""

import os
import sys
from pathlib import Path

# Add project root to path to enable imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

# This file now serves as a reference documentation for the banking API
# All route setup has been moved to routes.py to avoid circular imports


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

# This file now serves as a reference documentation for the banking API
# All route setup has been moved to routes.py to avoid circular imports
