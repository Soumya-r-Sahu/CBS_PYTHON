"""
Integration module for the HR-ERP System.

This module provides interfaces for integrating the HR-ERP module with other 
CBS (Core Banking System) modules for seamless data exchange and operations.
"""

from .integration_manager import IntegrationManager


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
__all__ = ['IntegrationManager']
