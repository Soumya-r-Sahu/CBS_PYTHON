"""
Audit service interface for security event logging.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional


class AuditService(ABC):
    """Interface for security audit logging."""
    
    @abstractmethod
    def log_authentication_event(
        self, 
        event_type: str,
        username: str,
        success: bool,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an authentication event.
        
        Args:
            event_type: Type of authentication event (e.g., "LOGIN", "LOGOUT", "PASSWORD_CHANGE")
            username: The username associated with the event
            success: Whether the authentication action was successful
            ip_address: The IP address where the request originated
            details: Additional details about the event
        """
        pass
    
    @abstractmethod
    def log_authorization_event(
        self,
        username: str,
        resource: str,
        action: str,
        success: bool,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an authorization event.
        
        Args:
            username: The username of the user performing the action
            resource: The resource being accessed
            action: The action being performed (e.g., "READ", "WRITE", "DELETE")
            success: Whether the authorization was successful
            ip_address: The IP address where the request originated
            details: Additional details about the event
        """
        pass
    
    @abstractmethod
    def log_security_event(
        self,
        event_type: str,
        description: str,
        severity: str,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a general security event.
        
        Args:
            event_type: Type of security event
            description: Description of the event
            severity: Severity level (e.g., "INFO", "WARNING", "ERROR", "CRITICAL")
            username: The username associated with the event, if applicable
            ip_address: The IP address where the request originated, if applicable
            details: Additional details about the event
        """
        pass
