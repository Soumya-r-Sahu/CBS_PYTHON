"""
Account Repository Interface

This module defines the interface for the account repository.
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...domain.entities.account import Account, AccountStatus, AccountType


class AccountRepositoryInterface(ABC):
    """Interface for account repository"""
    
    @abstractmethod
    def create(self, account: Account) -> Account:
        """
        Create a new account
        
        Args:
            account: The account to create
            
        Returns:
            The created account
        """
        pass
    
    @abstractmethod
    def get_by_id(self, account_id: UUID) -> Optional[Account]:
        """
        Get an account by ID
        
        Args:
            account_id: The account ID
            
        Returns:
            The account if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_account_number(self, account_number: str) -> Optional[Account]:
        """
        Get an account by account number
        
        Args:
            account_number: The account number
            
        Returns:
            The account if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_customer_id(self, customer_id: UUID) -> List[Account]:
        """
        Get accounts by customer ID
        
        Args:
            customer_id: The customer ID
            
        Returns:
            List of accounts
        """
        pass
    
    @abstractmethod
    def update(self, account: Account) -> Account:
        """
        Update an account
        
        Args:
            account: The account to update
            
        Returns:
            The updated account
        """
        pass
    
    @abstractmethod
    def update_balance(self, account_id: UUID, balance: Decimal) -> bool:
        """
        Update account balance
        
        Args:
            account_id: The account ID
            balance: The new balance
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def update_status(self, account_id: UUID, status: AccountStatus) -> bool:
        """
        Update account status
        
        Args:
            account_id: The account ID
            status: The new status
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, account_id: UUID) -> bool:
        """
        Delete an account
        
        Args:
            account_id: The account ID
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def search(self, 
              account_type: Optional[AccountType] = None,
              status: Optional[AccountStatus] = None,
              min_balance: Optional[Decimal] = None,
              max_balance: Optional[Decimal] = None,
              created_after: Optional[datetime] = None,
              created_before: Optional[datetime] = None) -> List[Account]:
        """
        Search accounts by criteria
        
        Args:
            account_type: Filter by account type
            status: Filter by account status
            min_balance: Minimum balance
            max_balance: Maximum balance
            created_after: Created after date
            created_before: Created before date
            
        Returns:
            List of matching accounts
        """
        pass
