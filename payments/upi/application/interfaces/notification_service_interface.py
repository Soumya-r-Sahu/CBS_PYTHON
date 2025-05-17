"""
Notification service interface for UPI transactions.
This interface defines the notification contract that infrastructure layer must implement.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

from ...domain.entities.upi_transaction import UpiTransaction


class UpiNotificationServiceInterface(ABC):
    """Interface for UPI notification services."""
    
    @abstractmethod
    def send_transaction_initiated_notification(self, transaction: UpiTransaction, to_vpa: str) -> bool:
        """
        Send notification for transaction initiation.
        
        Args:
            transaction: The UPI transaction that was initiated
            to_vpa: The VPA to send the notification to
            
        Returns:
            Boolean indicating if notification was sent successfully
        """
        pass
    
    @abstractmethod
    def send_transaction_completed_notification(self, transaction: UpiTransaction) -> Dict[str, bool]:
        """
        Send notification for transaction completion to both sender and receiver.
        
        Args:
            transaction: The UPI transaction that was completed
            
        Returns:
            Dictionary with notification status for sender and receiver
            Example: {'sender': True, 'receiver': True}
        """
        pass
    
    @abstractmethod
    def send_transaction_failed_notification(self, transaction: UpiTransaction) -> bool:
        """
        Send notification for transaction failure.
        
        Args:
            transaction: The UPI transaction that failed
            
        Returns:
            Boolean indicating if notification was sent successfully
        """
        pass
    
    @abstractmethod
    def send_reversal_notification(self, transaction: UpiTransaction) -> Dict[str, bool]:
        """
        Send notification for transaction reversal to both sender and receiver.
        
        Args:
            transaction: The UPI transaction that was reversed
            
        Returns:
            Dictionary with notification status for sender and receiver
            Example: {'sender': True, 'receiver': True}
        """
        pass
