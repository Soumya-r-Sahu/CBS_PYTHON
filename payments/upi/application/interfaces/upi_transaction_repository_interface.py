"""
UPI transaction repository interface in the application layer.
This interface defines the repository contract that the infrastructure layer must implement.
"""
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from ...domain.entities.upi_transaction import UpiTransaction, UpiTransactionStatus


class UpiTransactionRepositoryInterface(ABC):
    """Interface for UPI transaction repository."""
    
    @abstractmethod
    def save(self, transaction: UpiTransaction) -> None:
        """
        Save a UPI transaction to the repository.
        
        Args:
            transaction: The UPI transaction to save
        """
        pass
    
    @abstractmethod
    def get_by_id(self, transaction_id: UUID) -> Optional[UpiTransaction]:
        """
        Get a UPI transaction by ID.
        
        Args:
            transaction_id: The ID of the transaction to retrieve
            
        Returns:
            UpiTransaction if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update(self, transaction: UpiTransaction) -> None:
        """
        Update an existing UPI transaction.
        
        Args:
            transaction: The UPI transaction to update
        """
        pass
    
    @abstractmethod
    def get_transactions_by_vpa(self, vpa: str, 
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               status: Optional[UpiTransactionStatus] = None) -> List[UpiTransaction]:
        """
        Get transactions by VPA with optional filters.
        
        Args:
            vpa: VPA to search for (as sender or receiver)
            start_date: Optional start date filter
            end_date: Optional end date filter
            status: Optional status filter
            
        Returns:
            List of UPI transactions matching the criteria
        """
        pass
    
    @abstractmethod
    def get_daily_transaction_total(self, vpa: str, transaction_date: date) -> float:
        """
        Get the total amount of transactions for a VPA on a specific date.
        
        Args:
            vpa: VPA to calculate total for
            transaction_date: Date to calculate total for
            
        Returns:
            Total amount of transactions
        """
        pass
