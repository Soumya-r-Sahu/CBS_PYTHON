"""
Application Interfaces

This module exports the application interfaces for the ATM module.
"""

from .atm_repository import AtmRepositoryInterface as AtmRepository
from .notification_service import NotificationServiceInterface

__all__ = ['AtmRepository', 'NotificationServiceInterface']