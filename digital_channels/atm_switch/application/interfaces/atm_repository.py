"""
ATM Repository Interface

This module defines the repository interfaces for the ATM module.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import datetime, date

from ...domain.entities import AtmCard, Account, AtmSession, Transaction

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class AtmRepositoryInterface(ABC):
    """Interface for ATM repository operations"""
    
    @abstractmethod
    def get_card_by_number(self, card_number: str) -> Optional[AtmCard]:
        """
        Get card by card number
        
        Args:
            card_number: Card number to look up
            
        Returns:
            Card entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """
        Get account by ID
        
        Args:
            account_id: Account ID to look up
            
        Returns:
            Account entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update_card_status(self, card: AtmCard) -> bool:
        """
        Update card status
        
        Args:
            card: Card entity with updated status
            
        Returns:
            True if update successful, False otherwise
        """
        pass
    
    @abstractmethod
    def update_account_balance(self, account: Account) -> bool:
        """
        Update account balance
        
        Args:
            account: Account entity with updated balance
            
        Returns:
            True if update successful, False otherwise
        """
        pass
    
    @abstractmethod
    def create_transaction(self, transaction: Transaction) -> bool:
        """
        Create a new transaction record
        
        Args:
            transaction: Transaction entity to create
            
        Returns:
            True if creation successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_transactions_by_account(
        self, 
        account_id: int, 
        limit: int = 10
    ) -> List[Transaction]:
        """
        Get recent transactions for an account
        
        Args:
            account_id: Account ID to look up
            limit: Maximum number of transactions to return
            
        Returns:
            List of transactions
        """
        pass
    
    @abstractmethod
    def get_today_withdrawals(self, account_id: int) -> Decimal:
        """
        Get total withdrawals made today
        
        Args:
            account_id: Account ID to check
            
        Returns:
            Total withdrawal amount for today
        """
        pass
    
    @abstractmethod
    def store_atm_session(self, session: AtmSession) -> bool:
        """
        Store ATM session
        
        Args:
            session: ATM session to store
            
        Returns:
            True if storage successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_atm_session(self, session_token: str) -> Optional[AtmSession]:
        """
        Get ATM session by token
        
        Args:
            session_token: Session token to look up
            
        Returns:
            ATM session if found, None otherwise
        """
        pass
    
    @abstractmethod
    def remove_atm_session(self, session_token: str) -> bool:
        """
        Remove ATM session
        
        Args:
            session_token: Session token to remove
            
        Returns:
            True if removal successful, False otherwise
        """
        pass
