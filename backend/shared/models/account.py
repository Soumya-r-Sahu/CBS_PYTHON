"""
Account Model for Core Banking System V3.0
"""

from sqlalchemy import Column, String, Numeric, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from decimal import Decimal
import enum

from .base import BaseModel

class AccountType(enum.Enum):
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    RECURRING_DEPOSIT = "RECURRING_DEPOSIT"
    LOAN = "LOAN"

class AccountStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"
    DORMANT = "DORMANT"

class Account(BaseModel):
    """Account model for bank accounts"""
    __tablename__ = "accounts"
    
    # Account Information
    account_number = Column(String(20), unique=True, nullable=False)  # AC-YYYYMMDD-XXXXX
    account_type = Column(Enum(AccountType), nullable=False)
    
    # Customer Reference
    customer_id = Column(ForeignKey("customers.id"), nullable=False)
    
    # Financial Information
    balance = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    available_balance = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    
    # Interest and Limits
    interest_rate = Column(Numeric(5, 4), default=Decimal('0.0000'))
    minimum_balance = Column(Numeric(15, 2), default=Decimal('1000.00'))
    daily_limit = Column(Numeric(15, 2), default=Decimal('50000.00'))
    
    # Branch Information
    branch_code = Column(String(10), nullable=False)
    ifsc_code = Column(String(11), nullable=False)
    
    # Account Status
    status = Column(Enum(AccountStatus), default=AccountStatus.ACTIVE)
    last_transaction_date = Column(DateTime)
    
    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", lazy="dynamic")
    
    def can_withdraw(self, amount: Decimal) -> bool:
        """Check if withdrawal amount is allowed"""
        return self.available_balance >= amount and amount <= self.daily_limit
    
    def update_balance(self, amount: Decimal, transaction_type: str):
        """Update account balance based on transaction type"""
        if transaction_type in ['DEPOSIT', 'CREDIT']:
            self.balance += amount
            self.available_balance += amount
        elif transaction_type in ['WITHDRAWAL', 'DEBIT']:
            self.balance -= amount
            self.available_balance -= amount
    
    def get_balance_info(self):
        """Get balance information"""
        return {
            'balance': float(self.balance),
            'available_balance': float(self.available_balance),
            'currency': self.currency
        }
