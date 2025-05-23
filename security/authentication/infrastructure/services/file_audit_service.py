"""
File-based implementation of AuditService for security event logging.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from security.authentication.domain.services.audit_service import AuditService


class FileAuditService(AuditService):
    """File-based implementation of AuditService."""
    
    def __init__(self, log_file_path: str):
        """Initialize the audit service with file path.
        
        Args:
            log_file_path: Path to the audit log file
        """
        self.log_file_path = log_file_path
        self._configure_logger()
    
    def _configure_logger(self) -> None:
        """Configure the logger for audit logging."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        
        # Configure logger
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("security_audit")
        
        # Add file handler
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
    
    def _format_log_entry(self, log_data: Dict[str, Any]) -> str:
        """Format log data as JSON string.
        
        Args:
            log_data: Dictionary containing log information
            
        Returns:
            JSON formatted log entry
        """
        # Add timestamp if not present
        if 'timestamp' not in log_data:
            log_data['timestamp'] = datetime.now().isoformat()
            
        return json.dumps(log_data)
    
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
        log_data = {
            "type": "AUTHENTICATION",
            "event": event_type,
            "username": username,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if ip_address:
            log_data["ip_address"] = ip_address
            
        if details:
            log_data["details"] = details
            
        log_level = logging.INFO if success else logging.WARNING
        self.logger.log(log_level, self._format_log_entry(log_data))
    
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
        log_data = {
            "type": "AUTHORIZATION",
            "username": username,
            "resource": resource,
            "action": action,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if ip_address:
            log_data["ip_address"] = ip_address
            
        if details:
            log_data["details"] = details
            
        log_level = logging.INFO if success else logging.WARNING
        self.logger.log(log_level, self._format_log_entry(log_data))
    
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
        log_data = {
            "type": "SECURITY",
            "event": event_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        
        if username:
            log_data["username"] = username
            
        if ip_address:
            log_data["ip_address"] = ip_address
            
        if details:
            log_data["details"] = details
        
        # Map severity to log level
        log_levels = {
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        log_level = log_levels.get(severity.upper(), logging.INFO)
        
        self.logger.log(log_level, self._format_log_entry(log_data))
