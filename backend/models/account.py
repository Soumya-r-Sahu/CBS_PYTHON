"""
Account model for banking accounts.
"""

import enum
from decimal import Decimal
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Numeric, ForeignKey, Integer, Enum, DateTime
from sqlalchemy.orm import relationship

from .base import BaseModel

class AccountType(enum.Enum):
    """Types of banking accounts."""
    SAVINGS = "savings"
    CURRENT = "current"
    FIXED_DEPOSIT = "fixed_deposit"
    LOAN = "loan"
    CREDIT = "credit"

class Account(BaseModel):
    """
    Account model representing banking accounts.
    """
    __tablename__ = "accounts"
    
    # Account identification
    account_number = Column(String(20), unique=True, nullable=False, index=True)
    account_type = Column(Enum(AccountType), nullable=False)
    
    # Financial information
    balance = Column(Numeric(15, 2), default=0.00, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    interest_rate = Column(Numeric(5, 2), default=0.00, nullable=True)
    
    # Account details
    branch_code = Column(String(10), nullable=False)
    ifsc_code = Column(String(11), nullable=False)
    
    # Limits and settings
    daily_withdrawal_limit = Column(Numeric(10, 2), default=50000.00)
    daily_transfer_limit = Column(Numeric(10, 2), default=100000.00)
    
    # Status and dates
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, SUSPENDED, CLOSED
    opened_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_transaction_date = Column(DateTime, nullable=True)
    
    # Foreign keys
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    @property
    def balance_inr(self) -> str:
        """Get balance formatted as INR."""
        return f"₹{self.balance:,.2f}"
    
    @property
    def is_active(self) -> bool:
        """Check if account is active."""
        return self.status == "ACTIVE"
    
    @property
    def is_savings_account(self) -> bool:
        """Check if this is a savings account."""
        return self.account_type == AccountType.SAVINGS
    
    @property
    def is_current_account(self) -> bool:
        """Check if this is a current account."""
        return self.account_type == AccountType.CURRENT
    
    def can_withdraw(self, amount: Decimal) -> bool:
        """Check if withdrawal amount is allowed."""
        if not self.is_active:
            return False
        if amount <= 0:
            return False
        if amount > self.balance:
            return False
        if amount > self.daily_withdrawal_limit:
            return False
        return True
    
    def can_transfer(self, amount: Decimal) -> bool:
        """Check if transfer amount is allowed."""
        if not self.is_active:
            return False
        if amount <= 0:
            return False
        if amount > self.balance:
            return False
        if amount > self.daily_transfer_limit:
            return False
        return True
    
    def __repr__(self) -> str:
        return f"<Account(account_number={self.account_number}, type={self.account_type.value}, balance={self.balance})>"
