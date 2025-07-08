"""
User and Authentication Models for Core Banking System V3.0
"""

from sqlalchemy import Column, String, Enum, DateTime, Boolean, Text, Integer
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
import enum

from .base import BaseModel

# Password encryption context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    CASHIER = "CASHIER"
    CUSTOMER_SERVICE = "CUSTOMER_SERVICE"
    AUDITOR = "AUDITOR"
    CUSTOMER = "CUSTOMER"

class UserStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    LOCKED = "LOCKED"

class User(BaseModel):
    """User model for system authentication and authorization"""
    __tablename__ = "users"
    
    # User Information
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Personal Information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    employee_id = Column(String(20), unique=True)  # For bank employees
    
    # Role and Permissions
    role = Column(Enum(UserRole), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    
    # Security Information
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    password_changed_at = Column(DateTime)
    must_change_password = Column(Boolean, default=False)
    
    # Contact Information
    phone = Column(String(20))
    branch_code = Column(String(10))  # For bank employees
    
    # Account Settings
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    
    # Audit Fields
    created_by = Column(String(50))
    notes = Column(Text)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = pwd_context.hash(password)
    
    def check_password(self, password):
        """Check password"""
        return pwd_context.verify(password, self.password_hash)
    
    def get_full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    def is_employee(self):
        """Check if user is bank employee"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.CASHIER, UserRole.CUSTOMER_SERVICE, UserRole.AUDITOR]
    
    def can_access_admin_panel(self):
        """Check if user can access admin panel"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def is_account_locked(self):
        """Check if account is locked"""
        return self.status == UserStatus.LOCKED or self.failed_login_attempts >= 5
