"""
Audit logging service interface for the Internet Banking domain.
This interface defines methods for logging security and audit events.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID


class AuditEventType(Enum):
    """Types of audit events that can be logged."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    FAILED_LOGIN = "failed_login"
    PASSWORD_CHANGE = "password_change"
    PROFILE_UPDATE = "profile_update"
    ACCOUNT_ACCESS = "account_access"
    TRANSACTION_INITIATED = "transaction_initiated"
    TRANSACTION_COMPLETED = "transaction_completed"
    TRANSACTION_FAILED = "transaction_failed"
    SECURITY_SETTING_CHANGE = "security_setting_change"
    USER_LOCKED = "user_locked"
    USER_UNLOCKED = "user_unlocked"


class AuditLogServiceInterface(ABC):
    """Interface for audit logging operations."""
    
    @abstractmethod
    def log_event(
        self, 
        event_type: AuditEventType,
        user_id: Optional[UUID],
        session_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event being logged
            user_id: ID of the user associated with the event (if applicable)
            session_id: ID of the session in which the event occurred (if applicable)
            ip_address: IP address from which the event originated (if applicable)
            details: Additional details about the event
            status: Status of the event (success, failure, etc.)
            metadata: Additional metadata about the event
            
        Returns:
            Boolean indicating if the event was logged successfully
        """
        pass
    
    @abstractmethod
    def get_user_activity_log(
        self,
        user_id: UUID,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None,
        event_types: Optional[list] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """
        Get a log of user activity.
        
        Args:
            user_id: ID of the user
            from_timestamp: Optional start timestamp for filtering
            to_timestamp: Optional end timestamp for filtering
            event_types: Optional list of event types to filter by
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of audit log entries
        """
        pass
    
    @abstractmethod
    def get_security_events(
        self,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """
        Get a log of security events.
        
        Args:
            from_timestamp: Optional start timestamp for filtering
            to_timestamp: Optional end timestamp for filtering
            severity: Optional severity level for filtering
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of security event log entries
        """
        pass
