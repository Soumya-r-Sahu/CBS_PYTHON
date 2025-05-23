"""
User Entity

This module defines the User entity that represents
a user in the authentication domain. It encapsulates
business rules and invariants related to users.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..value_objects.user_id import UserId
from ..value_objects.credential import Credential
from ..value_objects.user_status import UserStatus


@dataclass
class User:
    """
    User entity representing a system user
    
    This is a core domain entity that contains user data
    and business logic related to user authentication.
    """
    username: str
    credentials: Credential
    status: UserStatus
    first_name: str
    last_name: str
    email: str
    user_id: UserId
    roles: List[str] = field(default_factory=list)
    mfa_enabled: bool = False
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None
    id: UUID = field(default_factory=uuid4)
    
    def __post_init__(self):
        """Validate user data during initialization"""
        self._validate()
    
    def _validate(self) -> None:
        """Validate user data"""
        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")
            
        if not self.email or '@' not in self.email:
            raise ValueError("Invalid email address")
    
    def authenticate(self, password: str) -> bool:
        """
        Authenticate user with password
        
        Args:
            password: Password to verify
            
        Returns:
            True if authentication successful, False otherwise
        """
        # Check if account is locked
        if self.is_locked():
            return False
        
        # Verify password
        if self.credentials.verify_password(password):
            self.login_attempts = 0
            self.last_login = datetime.now()
            return True
        else:
            self._increment_failed_attempts()
            return False
    
    def is_locked(self) -> bool:
        """
        Check if user account is locked
        
        Returns:
            True if locked, False otherwise
        """
        if self.locked_until and datetime.now() < self.locked_until:
            return True
        
        if self.locked_until and datetime.now() >= self.locked_until:
            # Auto-unlock if lock period expired
            self.locked_until = None
            self.login_attempts = 0
            
        return False
    
    def _increment_failed_attempts(self) -> None:
        """Increment failed login attempts and lock account if threshold reached"""
        self.login_attempts += 1
        
        # Lock account after 5 failed attempts
        if self.login_attempts >= 5:
            # Lock for 30 minutes
            self.locked_until = datetime.now().replace(
                minute=datetime.now().minute + 30
            )
    
    def has_role(self, role: str) -> bool:
        """
        Check if user has a specific role
        
        Args:
            role: Role to check
            
        Returns:
            True if user has the role, False otherwise
        """
        return role in self.roles
    
    def add_role(self, role: str) -> None:
        """
        Add a role to the user
        
        Args:
            role: Role to add
        """
        if role not in self.roles:
            self.roles.append(role)
    
    def remove_role(self, role: str) -> None:
        """
        Remove a role from the user
        
        Args:
            role: Role to remove
        """
        if role in self.roles:
            self.roles.remove(role)
    
    def change_password(self, new_password: str) -> None:
        """
        Change user password
        
        Args:
            new_password: New password
        """
        self.credentials.update_password(new_password)
    
    def enable_mfa(self) -> None:
        """Enable multi-factor authentication"""
        self.mfa_enabled = True
    
    def disable_mfa(self) -> None:
        """Disable multi-factor authentication"""
        self.mfa_enabled = False
    
    def lock_account(self) -> None:
        """Lock user account"""
        # Lock for 24 hours
        self.locked_until = datetime.now().replace(
            hour=datetime.now().hour + 24
        )
    
    def unlock_account(self) -> None:
        """Unlock user account"""
        self.locked_until = None
        self.login_attempts = 0
