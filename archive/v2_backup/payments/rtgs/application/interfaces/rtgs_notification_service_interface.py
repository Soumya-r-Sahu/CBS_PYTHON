"""
RTGS Notification Service Interface.
This interface defines the contract for notification services.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from uuid import UUID

from ...domain.entities.rtgs_transaction import RTGSTransaction


class RTGSNotificationServiceInterface(ABC):
    """Interface for RTGS notification service."""
    
    @abstractmethod
    def notify_transaction_initiated(self, transaction: RTGSTransaction) -> Dict[str, Any]:
        """
        Send notification for transaction initiation.
        
        Args:
            transaction: The initiated transaction
            
        Returns:
            Dict[str, Any]: Notification result
        """
        pass
    
    @abstractmethod
    def notify_transaction_completed(self, transaction: RTGSTransaction) -> Dict[str, Any]:
        """
        Send notification for transaction completion.
        
        Args:
            transaction: The completed transaction
            
        Returns:
            Dict[str, Any]: Notification result
        """
        pass
    
    @abstractmethod
    def notify_transaction_failed(self, transaction: RTGSTransaction, reason: str) -> Dict[str, Any]:
        """
        Send notification for transaction failure.
        
        Args:
            transaction: The failed transaction
            reason: Reason for failure
            
        Returns:
            Dict[str, Any]: Notification result
        """
        pass
    
    @abstractmethod
    def notify_transaction_returned(self, transaction: RTGSTransaction, return_reason: str) -> Dict[str, Any]:
        """
        Send notification for transaction return.
        
        Args:
            transaction: The returned transaction
            return_reason: Reason for return
            
        Returns:
            Dict[str, Any]: Notification result
        """
        pass
