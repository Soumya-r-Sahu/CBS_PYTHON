"""
Account Entity

This module defines the Account entity for the Core Banking System.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal


@dataclass
class Account:
    """Entity representing a bank account"""
    
    account_id: int
    account_number: str
    customer_id: int
    balance: Decimal
    account_type: Literal["SAVINGS", "CURRENT", "FIXED_DEPOSIT", "LOAN"]
    currency: str = "INR"
    status: Literal["ACTIVE", "DORMANT", "CLOSED", "FROZEN"] = "ACTIVE"
    last_transaction_date: Optional[datetime] = None
    
    def is_active(self) -> bool:
        """Check if account is active"""
        return self.status == "ACTIVE"
    
    def has_sufficient_balance(self, amount: Decimal) -> bool:
        """Check if account has sufficient balance for transaction"""
        return self.balance >= amount
    
    def debit(self, amount: Decimal) -> bool:
        """
        Debit amount from account
        
        Args:
            amount: Amount to debit
            
        Returns:
            True if successful, False otherwise
        """
        if not self.has_sufficient_balance(amount):
            return False
            
        self.balance -= amount
        self.last_transaction_date = datetime.now()
        return True
    
    def credit(self, amount: Decimal) -> bool:
        """
        Credit amount to account
        
        Args:
            amount: Amount to credit
            
        Returns:
            True if successful, False otherwise
        """
        self.balance += amount
        self.last_transaction_date = datetime.now()
        return True
