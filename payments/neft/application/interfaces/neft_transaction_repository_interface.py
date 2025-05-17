"""
NEFT Transaction Repository Interface.
This interface defines the contract for transaction repositories.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ...domain.entities.neft_transaction import NEFTTransaction


class NEFTTransactionRepositoryInterface(ABC):
    """Interface for NEFT transaction repository."""
    
    @abstractmethod
    def get_by_id(self, transaction_id: UUID) -> Optional[NEFTTransaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: The transaction ID
            
        Returns:
            Optional[NEFTTransaction]: The transaction if found, None otherwise
        """
        pass
    
    @abstractmethod
    def save(self, transaction: NEFTTransaction) -> NEFTTransaction:
        """
        Save a transaction.
        
        Args:
            transaction: The transaction to save
            
        Returns:
            NEFTTransaction: The saved transaction
        """
        pass
    
    @abstractmethod
    def update(self, transaction: NEFTTransaction) -> NEFTTransaction:
        """
        Update a transaction.
        
        Args:
            transaction: The transaction to update
            
        Returns:
            NEFTTransaction: The updated transaction
        """
        pass
    
    @abstractmethod
    def get_by_customer_id(self, customer_id: str, limit: int = 10) -> List[NEFTTransaction]:
        """
        Get transactions by customer ID.
        
        Args:
            customer_id: The customer ID
            limit: Maximum number of transactions to return
            
        Returns:
            List[NEFTTransaction]: List of transactions
        """
        pass
    
    @abstractmethod
    def get_by_status(self, status: str, limit: int = 100) -> List[NEFTTransaction]:
        """
        Get transactions by status.
        
        Args:
            status: The transaction status
            limit: Maximum number of transactions to return
            
        Returns:
            List[NEFTTransaction]: List of transactions
        """
        pass
    
    @abstractmethod
    def get_by_batch_number(self, batch_number: str) -> List[NEFTTransaction]:
        """
        Get transactions by batch number.
        
        Args:
            batch_number: The batch number
            
        Returns:
            List[NEFTTransaction]: List of transactions
        """
        pass
