"""
Leave Management Package

This package contains modules for handling leave applications, approvals, and balances.
"""

from .leave_manager import LeaveManager, get_leave_manager


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
__all__ = ['LeaveManager', 'get_leave_manager']
