"""
Transaction Repository Interface

This module defines the interface for transaction repositories.
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...domain.entities.transaction import Transaction, TransactionStatus, TransactionType


class TransactionRepositoryInterface(ABC):
    """Interface for transaction repositories"""
    
    @abstractmethod
    def create(self, transaction: Transaction) -> Transaction:
        """
        Create a new transaction
        
        Args:
            transaction: Transaction to create
            
        Returns:
            Created transaction
            
        Raises:
            DatabaseException: If there was an error creating the transaction
        """
        pass
    
    @abstractmethod
    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """
        Get a transaction by ID
        
        Args:
            transaction_id: ID of the transaction
            
        Returns:
            Transaction if found, None otherwise
            
        Raises:
            DatabaseException: If there was an error retrieving the transaction
        """
        pass
    
    @abstractmethod
    def get_by_reference_number(self, reference_number: str) -> Optional[Transaction]:
        """
        Get a transaction by reference number
        
        Args:
            reference_number: Reference number of the transaction
            
        Returns:
            Transaction if found, None otherwise
            
        Raises:
            DatabaseException: If there was an error retrieving the transaction
        """
        pass
    
    @abstractmethod
    def update(self, transaction: Transaction) -> Transaction:
        """
        Update an existing transaction
        
        Args:
            transaction: Transaction to update
            
        Returns:
            Updated transaction
            
        Raises:
            DatabaseException: If there was an error updating the transaction
        """
        pass
    
    @abstractmethod
    def get_account_transactions(
        self, 
        account_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """
        Get transactions for a specific account
        
        Args:
            account_id: ID of the account
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            transaction_type: Filter by transaction type
            status: Filter by transaction status
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of transactions
            
        Raises:
            DatabaseException: If there was an error retrieving the transactions
        """
        pass
    
    @abstractmethod
    def get_transactions_by_date_range(
        self,
        start_date: date,
        end_date: date,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """
        Get all transactions within a date range
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of transactions
            
        Raises:
            DatabaseException: If there was an error retrieving the transactions
        """
        pass
