"""
User model for authentication and system access.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship

from .base import BaseModel

class UserRole(enum.Enum):
    """User roles in the banking system."""
    ADMIN = "admin"
    MANAGER = "manager"
    TELLER = "teller"
    CUSTOMER = "customer"
    AUDITOR = "auditor"

class User(BaseModel):
    """
    User model for system authentication and authorization.
    """
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    
    # Account status
    is_verified = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(String(10), default="0")
    last_login = Column(String(50), nullable=True)
    
    # Contact information
    phone = Column(String(20), nullable=True)
    
    def __repr__(self) -> str:
        return f"<User(username={self.username}, email={self.email}, role={self.role.value})>"
    
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN
    
    def is_manager(self) -> bool:
        """Check if user has manager role."""
        return self.role == UserRole.MANAGER
    
    def is_teller(self) -> bool:
        """Check if user has teller role."""
        return self.role == UserRole.TELLER
    
    def is_customer(self) -> bool:
        """Check if user has customer role."""
        return self.role == UserRole.CUSTOMER
    
    def can_access_admin_panel(self) -> bool:
        """Check if user can access admin panel."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_process_transactions(self) -> bool:
        """Check if user can process transactions."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.TELLER]
