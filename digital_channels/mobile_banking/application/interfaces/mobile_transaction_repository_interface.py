"""
Mobile Transaction repository interface for the Mobile Banking domain.
This interface defines methods for persisting and retrieving mobile banking transactions.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ...domain.entities.mobile_transaction import MobileTransaction


class MobileTransactionRepositoryInterface(ABC):
    """Interface for mobile transaction repository operations."""
    
    @abstractmethod
    def get_by_id(self, transaction_id: UUID) -> Optional[MobileTransaction]:
        """
        Get a transaction by its ID.
        
        Args:
            transaction_id: The ID of the transaction to get
            
        Returns:
            MobileTransaction if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_reference_number(self, reference_number: str) -> Optional[MobileTransaction]:
        """
        Get a transaction by its reference number.
        
        Args:
            reference_number: The reference number of the transaction to get
            
        Returns:
            MobileTransaction if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: UUID) -> List[MobileTransaction]:
        """
        Get all transactions for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of MobileTransaction objects
        """
        pass
    
    @abstractmethod
    def get_by_user_id_and_date_range(
        self, 
        user_id: UUID, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[MobileTransaction]:
        """
        Get all transactions for a user within a date range.
        
        Args:
            user_id: The ID of the user
            start_date: The start date of the range
            end_date: The end date of the range
            
        Returns:
            List of MobileTransaction objects
        """
        pass
    
    @abstractmethod
    def save(self, transaction: MobileTransaction) -> MobileTransaction:
        """
        Save a transaction to the repository.
        
        Args:
            transaction: The transaction to save
            
        Returns:
            The saved transaction with any updates (e.g., ID assignment)
        """
        pass
    
    @abstractmethod
    def update(self, transaction: MobileTransaction) -> MobileTransaction:
        """
        Update an existing transaction.
        
        Args:
            transaction: The transaction to update
            
        Returns:
            The updated transaction
        """
        pass
