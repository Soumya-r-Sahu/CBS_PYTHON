"""
UserStatus Value Object

This module defines the UserStatus value object which
represents the status of a user account in the system.
"""

from dataclasses import dataclass
from enum import Enum, auto


class Status(Enum):
    """Enumeration of possible user statuses"""
    ACTIVE = auto()
    INACTIVE = auto()
    PENDING = auto()
    LOCKED = auto()
    SUSPENDED = auto()


@dataclass(frozen=True)
class UserStatus:
    """
    Value object representing a user status
    
    This encapsulates the status of a user account
    and provides behavioral methods to check the status.
    """
    status: Status
    
    def __post_init__(self):
        """Validate the status"""
        if not isinstance(self.status, Status):
            object.__setattr__(self, 'status', Status[self.status])
    
    def is_active(self) -> bool:
        """
        Check if the status is active
        
        Returns:
            True if active, False otherwise
        """
        return self.status == Status.ACTIVE
    
    def is_inactive(self) -> bool:
        """
        Check if the status is inactive
        
        Returns:
            True if inactive, False otherwise
        """
        return self.status == Status.INACTIVE
    
    def is_pending(self) -> bool:
        """
        Check if the status is pending
        
        Returns:
            True if pending, False otherwise
        """
        return self.status == Status.PENDING
    
    def is_locked(self) -> bool:
        """
        Check if the status is locked
        
        Returns:
            True if locked, False otherwise
        """
        return self.status == Status.LOCKED
    
    def is_suspended(self) -> bool:
        """
        Check if the status is suspended
        
        Returns:
            True if suspended, False otherwise
        """
        return self.status == Status.SUSPENDED
    
    def can_login(self) -> bool:
        """
        Check if the user can login with this status
        
        Returns:
            True if can login, False otherwise
        """
        return self.status == Status.ACTIVE
    
    @staticmethod
    def active() -> 'UserStatus':
        """
        Create an active status
        
        Returns:
            Active user status
        """
        return UserStatus(Status.ACTIVE)
    
    @staticmethod
    def inactive() -> 'UserStatus':
        """
        Create an inactive status
        
        Returns:
            Inactive user status
        """
        return UserStatus(Status.INACTIVE)
    
    @staticmethod
    def pending() -> 'UserStatus':
        """
        Create a pending status
        
        Returns:
            Pending user status
        """
        return UserStatus(Status.PENDING)
    
    @staticmethod
    def locked() -> 'UserStatus':
        """
        Create a locked status
        
        Returns:
            Locked user status
        """
        return UserStatus(Status.LOCKED)
    
    @staticmethod
    def suspended() -> 'UserStatus':
        """
        Create a suspended status
        
        Returns:
            Suspended user status
        """
        return UserStatus(Status.SUSPENDED)
