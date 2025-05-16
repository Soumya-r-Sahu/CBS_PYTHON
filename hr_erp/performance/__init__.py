"""
Performance Management module for the HR-ERP System.

This module handles employee performance evaluations, goal setting,
performance reviews, and performance metrics analysis.
"""

from .performance_manager import PerformanceManager


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
__all__ = ['PerformanceManager']
