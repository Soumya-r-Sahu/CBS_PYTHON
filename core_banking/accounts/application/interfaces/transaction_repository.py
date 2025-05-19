"""
Transaction Repository Interface

This module defines the interface for the transaction repository.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...domain.entities.transaction import Transaction, TransactionType, TransactionStatus

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class TransactionRepositoryInterface(ABC):
    """Interface for transaction repository"""
    
    @abstractmethod
    def create(self, transaction: Transaction) -> Transaction:
        """
        Create a new transaction
        
        Args:
            transaction: The transaction to create
            
        Returns:
            The created transaction
        """
        pass
    
    @abstractmethod
    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """
        Get a transaction by ID
        
        Args:
            transaction_id: The transaction ID
            
        Returns:
            The transaction if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_account_id(self, 
                         account_id: str, 
                         limit: int = 10, 
                         offset: int = 0) -> List[Transaction]:
        """
        Get transactions by account ID
        
        Args:
            account_id: The account ID
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of transactions
        """
        pass
    
    @abstractmethod
    def get_by_reference_id(self, reference_id: str) -> List[Transaction]:
        """
        Get transactions by reference ID
        
        Args:
            reference_id: The reference ID
            
        Returns:
            List of transactions
        """
        pass
    
    @abstractmethod
    def update_status(self, transaction_id: UUID, status: TransactionStatus) -> bool:
        """
        Update transaction status
        
        Args:
            transaction_id: The transaction ID
            status: The new status
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def search(self,
              account_id: Optional[str] = None,
              transaction_type: Optional[TransactionType] = None,
              status: Optional[TransactionStatus] = None,
              min_amount: Optional[Decimal] = None,
              max_amount: Optional[Decimal] = None,
              start_date: Optional[datetime] = None,
              end_date: Optional[datetime] = None,
              limit: int = 100,
              offset: int = 0) -> List[Transaction]:
        """
        Search transactions by criteria
        
        Args:
            account_id: Filter by account ID
            transaction_type: Filter by transaction type
            status: Filter by transaction status
            min_amount: Minimum amount
            max_amount: Maximum amount
            start_date: Start date
            end_date: End date
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of matching transactions
        """
        pass
