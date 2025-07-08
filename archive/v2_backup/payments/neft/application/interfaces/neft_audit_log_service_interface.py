"""
NEFT Audit Log Service Interface.
This interface defines the contract for audit logging.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

from ...domain.entities.neft_transaction import NEFTTransaction
from ...domain.entities.neft_batch import NEFTBatch


class NEFTAuditLogServiceInterface(ABC):
    """Interface for NEFT audit log service."""
    
    @abstractmethod
    def log_transaction_created(self, transaction: NEFTTransaction, user_id: str = None) -> bool:
        """
        Log transaction creation event.
        
        Args:
            transaction: The created transaction
            user_id: ID of the user who created the transaction
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def log_transaction_updated(self, transaction: NEFTTransaction, previous_status: str, user_id: str = None) -> bool:
        """
        Log transaction update event.
        
        Args:
            transaction: The updated transaction
            previous_status: Previous status of the transaction
            user_id: ID of the user who updated the transaction
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def log_batch_created(self, batch: NEFTBatch, user_id: str = None) -> bool:
        """
        Log batch creation event.
        
        Args:
            batch: The created batch
            user_id: ID of the user who created the batch
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def log_batch_updated(self, batch: NEFTBatch, previous_status: str, user_id: str = None) -> bool:
        """
        Log batch update event.
        
        Args:
            batch: The updated batch
            previous_status: Previous status of the batch
            user_id: ID of the user who updated the batch
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def log_rbi_interface_event(self, event_type: str, details: Dict[str, Any], success: bool) -> bool:
        """
        Log RBI interface event.
        
        Args:
            event_type: Type of event (e.g., 'submit_transaction', 'check_status')
            details: Event details
            success: Whether the event was successful
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        pass
