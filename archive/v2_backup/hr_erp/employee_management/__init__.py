"""
Employee Management Package

This package contains modules for managing employee records, profiles, and related information.
"""

from .employee_manager import EmployeeManager, get_employee_manager


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
__all__ = ['EmployeeManager', 'get_employee_manager']
