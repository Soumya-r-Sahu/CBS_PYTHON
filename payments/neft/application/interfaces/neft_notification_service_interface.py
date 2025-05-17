"""
NEFT Notification Service Interface.
This interface defines the contract for notification services.
"""
from abc import ABC, abstractmethod

from ...domain.entities.neft_transaction import NEFTTransaction


class NEFTNotificationServiceInterface(ABC):
    """Interface for NEFT notification service."""
    
    @abstractmethod
    def notify_transaction_initiated(self, transaction: NEFTTransaction) -> bool:
        """
        Notify that a transaction has been initiated.
        
        Args:
            transaction: The transaction that was initiated
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def notify_transaction_completed(self, transaction: NEFTTransaction) -> bool:
        """
        Notify that a transaction has been completed.
        
        Args:
            transaction: The completed transaction
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def notify_transaction_failed(self, transaction: NEFTTransaction) -> bool:
        """
        Notify that a transaction has failed.
        
        Args:
            transaction: The failed transaction
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def notify_batch_completed(self, batch_number: str, success_count: int, fail_count: int) -> bool:
        """
        Notify that a batch has been completed.
        
        Args:
            batch_number: The batch number
            success_count: Number of successful transactions
            fail_count: Number of failed transactions
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        pass
