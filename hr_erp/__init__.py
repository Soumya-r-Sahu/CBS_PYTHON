"""
Core Banking System - HR-ERP Module

This module provides Human Resources and Enterprise Resource Planning functionality
for the Core Banking System. It includes employee management, payroll, recruitment,
performance evaluation, training and development, and integration with other
CBS modules.
"""

# Version information
__version__ = '1.1.0'

# Import submodules for easier access
# These imports assume each module has proper __init__.py files
from .employee_management import *
from .payroll import *
from .recruitment import *
from .leave import *
from .performance import *
from .training import *
from .integration import *

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
