"""
RTGS Transaction Repository Interface.
This interface defines the contract for transaction repositories.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ...domain.entities.rtgs_transaction import RTGSTransaction


class RTGSTransactionRepositoryInterface(ABC):
    """Interface for RTGS transaction repository."""
    
    @abstractmethod
    def get_by_id(self, transaction_id: UUID) -> Optional[RTGSTransaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: The transaction ID
            
        Returns:
            Optional[RTGSTransaction]: The transaction if found, None otherwise
        """
        pass
    
    @abstractmethod
    def save(self, transaction: RTGSTransaction) -> RTGSTransaction:
        """
        Save a transaction.
        
        Args:
            transaction: The transaction to save
            
        Returns:
            RTGSTransaction: The saved transaction
        """
        pass
    
    @abstractmethod
    def update(self, transaction: RTGSTransaction) -> RTGSTransaction:
        """
        Update a transaction.
        
        Args:
            transaction: The transaction to update
            
        Returns:
            RTGSTransaction: The updated transaction
        """
        pass
    
    @abstractmethod
    def get_by_customer_id(self, customer_id: str, limit: int = 10) -> List[RTGSTransaction]:
        """
        Get transactions by customer ID.
        
        Args:
            customer_id: The customer ID
            limit: Maximum number of transactions to return
            
        Returns:
            List[RTGSTransaction]: List of transactions
        """
        pass
    
    @abstractmethod
    def get_by_status(self, status: str, limit: int = 100) -> List[RTGSTransaction]:
        """
        Get transactions by status.
        
        Args:
            status: The transaction status
            limit: Maximum number of transactions to return
            
        Returns:
            List[RTGSTransaction]: List of transactions
        """
        pass
    
    @abstractmethod
    def get_by_date_range(self, start_date: str, end_date: str, limit: int = 100) -> List[RTGSTransaction]:
        """
        Get transactions by date range.
        
        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            limit: Maximum number of transactions to return
            
        Returns:
            List[RTGSTransaction]: List of transactions
        """
        pass
    
    @abstractmethod
    def get_by_utr_number(self, utr_number: str) -> Optional[RTGSTransaction]:
        """
        Get a transaction by UTR number.
        
        Args:
            utr_number: The Unique Transaction Reference number
            
        Returns:
            Optional[RTGSTransaction]: The transaction if found, None otherwise
        """
        pass
