"""
Shared Database Layer for Core Banking System V3.0

This module provides common database functionality for all microservices.
"""

from .connection import DatabaseManager, get_db_session
from .base import Base, BaseModel
from .models import *

__all__ = [
    "DatabaseManager",
    "get_db_session", 
    "Base",
    "BaseModel",
    "Customer",
    "Account", 
    "Transaction",
    "Branch",
    "Card",
    "Beneficiary",
    "StandingInstruction"
]
