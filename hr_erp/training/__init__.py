"""
Training and Development module for the HR-ERP System.

This module handles employee training programs, skill development initiatives,
career development planning, and training effectiveness tracking.
"""

from .training_manager import TrainingManager


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
__all__ = ['TrainingManager']
