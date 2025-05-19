"""
Account Entity

This module defines the Account entity representing a bank account.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class AccountType(Enum):
    """Account types"""
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    LOAN = "LOAN"


class AccountStatus(Enum):
    """Account status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"
    CLOSED = "CLOSED"


@dataclass
class Account:
    """
    Account entity
    
    Represents a bank account with all relevant properties.
    """
    account_number: str
    customer_id: UUID
    account_type: AccountType
    balance: Decimal = field(default=Decimal('0.00'))
    status: AccountStatus = AccountStatus.ACTIVE
    currency: str = "INR"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: UUID = field(default_factory=uuid4)
    interest_rate: Optional[Decimal] = None
    overdraft_limit: Optional[Decimal] = None

    def __post_init__(self):
        """
        Validate account after initialization
        
        Raises:
            ValueError: If any of the account properties are invalid
        """
        # Validate account_number (assume a specific format, e.g., starts with 'ACC' followed by numbers)
        if not self.account_number or not self.account_number.startswith('ACC'):
            raise ValueError("Account number must start with 'ACC' followed by numbers")
        
        # Validate balance is non-negative
        if self.balance < Decimal('0') and self.account_type != AccountType.LOAN:
            raise ValueError("Initial balance cannot be negative for non-loan accounts")
            
        # Validate currency code (assume ISO 4217 - 3 letter codes)
        if not self.currency or len(self.currency.strip()) != 3:
            raise ValueError("Currency must be a valid 3-letter ISO currency code")
        
        # Specific validations based on account type
        if self.account_type == AccountType.FIXED_DEPOSIT and self.balance <= Decimal('0'):
            raise ValueError("Fixed deposit accounts must have a positive initial balance")
            
        if self.account_type == AccountType.CURRENT and self.overdraft_limit is None:
            # Set a default overdraft limit for current accounts
            self.overdraft_limit = Decimal('10000.00')
    
    def deposit(self, amount: Decimal) -> bool:
        """
        Deposit money into the account
        
        Args:
            amount: The amount to deposit
            
        Returns:
            True if the deposit was successful, False otherwise
        
        Raises:
            ValueError: If the amount is negative or zero
        """
        if amount <= Decimal('0'):
            raise ValueError("Deposit amount must be positive")
            
        if self.status != AccountStatus.ACTIVE:
            return False
            
        self.balance += amount
        self.updated_at = datetime.now()
        return True
    
    def withdraw(self, amount: Decimal) -> bool:
        """
        Withdraw money from the account
        
        Args:
            amount: The amount to withdraw
            
        Returns:
            True if the withdrawal was successful, False otherwise
            
        Raises:
            ValueError: If the amount is negative or zero
        """
        if amount <= Decimal('0'):
            raise ValueError("Withdrawal amount must be positive")
            
        if self.status != AccountStatus.ACTIVE:
            return False
            
        available_balance = self.balance
        if self.overdraft_limit:
            available_balance += self.overdraft_limit
            
        if amount > available_balance:
            return False
            
        self.balance -= amount
        self.updated_at = datetime.now()
        return True
        
    def close(self) -> bool:
        """
        Close the account
        
        Returns:
            True if the account was successfully closed, False otherwise
        """
        if self.balance != Decimal('0'):
            return False  # Cannot close account with non-zero balance
            
        self.status = AccountStatus.CLOSED
        self.updated_at = datetime.now()
        return True
        
    def reactivate(self) -> bool:
        """
        Reactivate a closed or inactive account
        
        Returns:
            True if the account was successfully reactivated, False otherwise
        """
        if self.status == AccountStatus.BLOCKED:
            return False  # Blocked accounts need manual intervention
            
        self.status = AccountStatus.ACTIVE
        self.updated_at = datetime.now()
        return True
        
    def block(self) -> bool:
        """
        Block the account
        
        Returns:
            True if the account was blocked successfully, False otherwise
        """
        if self.status == AccountStatus.BLOCKED:
            return False
            
        self.status = AccountStatus.BLOCKED
        self.updated_at = datetime.now()
        return True
        
    def is_active(self) -> bool:
        """
        Check if the account is active
        
        Returns:
            True if the account is active, False otherwise
        """
        return self.status == AccountStatus.ACTIVE
        
    def can_withdraw(self, amount: Decimal) -> bool:
        """
        Check if a withdrawal of the given amount is allowed
        
        Args:
            amount: The amount to withdraw
            
        Returns:
            True if the withdrawal is allowed, False otherwise
        """
        if not self.is_active():
            return False
            
        if amount <= Decimal('0'):
            return False
            
        available_balance = self.balance
        if self.overdraft_limit:
            available_balance += self.overdraft_limit
            
        return amount <= available_balance
        
    def can_deposit(self, amount: Decimal) -> bool:
        """
        Check if a deposit of the given amount is allowed
        
        Args:
            amount: The amount to deposit
            
        Returns:
            True if the deposit is allowed, False otherwise
        """
        return self.is_active() and amount > Decimal('0')
