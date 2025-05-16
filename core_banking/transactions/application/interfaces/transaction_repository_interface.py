"""
Transaction Repository Interface

Defines the interface for transaction data access.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...domain.entities.transaction import Transaction, TransactionStatus, TransactionType

class TransactionRepositoryInterface(ABC):
    """Interface for transaction data access operations"""
    
    @abstractmethod
    def save(self, transaction: Transaction) -> Transaction:
        """
        Save a transaction
        
        Args:
            transaction: Transaction to save
            
        Returns:
            Saved transaction with any system-generated fields populated
        """
        pass
    
    @abstractmethod
    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """
        Get transaction by ID
        
        Args:
            transaction_id: Transaction ID to retrieve
            
        Returns:
            Transaction if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_account_id(self, account_id: UUID, limit: int = 10, offset: int = 0) -> List[Transaction]:
        """
        Get transactions for an account
        
        Args:
            account_id: Account ID to retrieve transactions for
            limit: Maximum number of transactions to return
            offset: Offset for pagination
            
        Returns:
            List of transactions for the account
        """
        pass
    
    @abstractmethod
    def update_status(self, transaction_id: UUID, status: TransactionStatus) -> Optional[Transaction]:
        """
        Update transaction status
        
        Args:
            transaction_id: Transaction ID to update
            status: New status
            
        Returns:
            Updated transaction if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_account_daily_total(self, account_id: UUID, transaction_type: TransactionType, date: datetime) -> Decimal:
        """
        Get total transaction amount for an account on a specific date and type
        
        Args:
            account_id: Account ID to check
            transaction_type: Type of transactions to total
            date: Date to check
            
        Returns:
            Total transaction amount
        """
        pass
    
    @abstractmethod
    def search(self, criteria: Dict[str, Any], limit: int = 10, offset: int = 0) -> List[Transaction]:
        """
        Search transactions by criteria
        
        Args:
            criteria: Search criteria
            limit: Maximum number of transactions to return
            offset: Offset for pagination
            
        Returns:
            List of matching transactions
        """
        pass
