"""
RTGS Audit Log Service Interface.
This interface defines the contract for audit logging services.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from uuid import UUID

from ...domain.entities.rtgs_transaction import RTGSTransaction
from ...domain.entities.rtgs_batch import RTGSBatch


class RTGSAuditLogServiceInterface(ABC):
    """Interface for RTGS audit log service."""
    
    @abstractmethod
    def log_transaction_created(self, transaction: RTGSTransaction, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Log transaction creation event.
        
        Args:
            transaction: The created transaction
            user_id: ID of the user who created the transaction
            
        Returns:
            Dict[str, Any]: Log result
        """
        pass
    
    @abstractmethod
    def log_transaction_updated(self, transaction: RTGSTransaction, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Log transaction update event.
        
        Args:
            transaction: The updated transaction
            user_id: ID of the user who updated the transaction
            
        Returns:
            Dict[str, Any]: Log result
        """
        pass
    
    @abstractmethod
    def log_transaction_status_changed(self, transaction: RTGSTransaction, old_status: str, new_status: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Log transaction status change event.
        
        Args:
            transaction: The transaction with changed status
            old_status: Previous status
            new_status: New status
            user_id: ID of the user who changed the status
            
        Returns:
            Dict[str, Any]: Log result
        """
        pass
    
    @abstractmethod
    def log_batch_created(self, batch: RTGSBatch, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Log batch creation event.
        
        Args:
            batch: The created batch
            user_id: ID of the user who created the batch
            
        Returns:
            Dict[str, Any]: Log result
        """
        pass
    
    @abstractmethod
    def log_batch_updated(self, batch: RTGSBatch, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Log batch update event.
        
        Args:
            batch: The updated batch
            user_id: ID of the user who updated the batch
            
        Returns:
            Dict[str, Any]: Log result
        """
        pass
    
    @abstractmethod
    def log_batch_status_changed(self, batch: RTGSBatch, old_status: str, new_status: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Log batch status change event.
        
        Args:
            batch: The batch with changed status
            old_status: Previous status
            new_status: New status
            user_id: ID of the user who changed the status
            
        Returns:
            Dict[str, Any]: Log result
        """
        pass
