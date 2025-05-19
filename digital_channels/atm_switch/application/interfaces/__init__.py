# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

"""
Application Interfaces

This module exports the application interfaces for the ATM module.
"""

from .atm_repository import AtmRepositoryInterface as AtmRepository
from .notification_service import NotificationServiceInterface

__all__ = ['AtmRepository', 'NotificationServiceInterface']