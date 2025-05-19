"""
Audit log service interface for the Mobile Banking domain.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class AuditEventType(Enum):
    """Types of audit events that can be logged."""
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"
    PASSWORD_CHANGE = "password_change"
    TRANSACTION_INITIATED = "transaction_initiated"
    TRANSACTION_COMPLETED = "transaction_completed"
    TRANSACTION_FAILED = "transaction_failed"
    PROFILE_UPDATE = "profile_update"
    DEVICE_REGISTRATION = "device_registration"
    SECURITY_SETTING_CHANGE = "security_setting_change"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SESSION_EXPIRED = "session_expired"
    SESSION_EXTENDED = "session_extended"
    BENEFICIARY_ADDED = "beneficiary_added"
    BENEFICIARY_REMOVED = "beneficiary_removed"


class AuditLogServiceInterface(ABC):
    """Interface for audit log service operations."""
    
    @abstractmethod
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[UUID],
        ip_address: str,
        details: Dict[str, Any],
        status: str,
        device_info: Optional[Dict[str, Any]] = None,
        location: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Log an audit event.
        
        Args:
            event_type: The type of event to log
            user_id: The ID of the user involved
            ip_address: The IP address from which the event originated
            details: Details about the event
            status: Status of the event (success, failure, etc.)
            device_info: Information about the device used
            location: Location information
            timestamp: The time of the event (defaults to now)
            
        Returns:
            True if event was logged, False otherwise
        """
        pass
    
    @abstractmethod
    def get_user_events(
        self,
        user_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[list[AuditEventType]] = None
    ) -> list[Dict[str, Any]]:
        """
        Get audit events for a user.
        
        Args:
            user_id: The ID of the user
            start_time: The start time of the range
            end_time: The end time of the range
            event_types: Only include these event types
            
        Returns:
            List of audit events as dictionaries
        """
        pass
    
    @abstractmethod
    def get_system_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[list[AuditEventType]] = None,
        status: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Get audit events for the system.
        
        Args:
            start_time: The start time of the range
            end_time: The end time of the range
            event_types: Only include these event types
            status: Only include events with this status
            
        Returns:
            List of audit events as dictionaries
        """
        pass
