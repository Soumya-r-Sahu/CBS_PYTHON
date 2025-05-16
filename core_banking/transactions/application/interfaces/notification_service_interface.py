"""
Notification Service Interface

Defines the interface for sending transaction notifications.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from uuid import UUID

from ...domain.entities.transaction import Transaction

class NotificationServiceInterface(ABC):
    """Interface for notification services"""
    
    @abstractmethod
    def send_transaction_notification(self, transaction: Transaction, account_data: Dict[str, Any]) -> bool:
        """
        Send a notification for a transaction
        
        Args:
            transaction: Transaction to send notification for
            account_data: Account data including customer information
            
        Returns:
            True if notification was sent successfully
        """
        pass
    
    @abstractmethod
    def send_error_notification(self, transaction_id: Optional[UUID], error: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send an error notification
        
        Args:
            transaction_id: Transaction ID if available
            error: Error message
            metadata: Additional error metadata
            
        Returns:
            True if notification was sent successfully
        """
        pass
    
    @abstractmethod
    def send_security_alert(self, account_id: UUID, alert_type: str, details: Dict[str, Any]) -> bool:
        """
        Send a security alert
        
        Args:
            account_id: Account ID
            alert_type: Type of security alert
            details: Alert details
            
        Returns:
            True if alert was sent successfully
        """
        pass
