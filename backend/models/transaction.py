"""
Transaction model for banking transactions.
"""

import enum
from decimal import Decimal
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Numeric, ForeignKey, Integer, Enum, DateTime, Text
from sqlalchemy.orm import relationship

from .base import BaseModel

class TransactionType(enum.Enum):
    """Types of banking transactions."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    INTEREST_CREDIT = "interest_credit"
    FEE_DEBIT = "fee_debit"
    REFUND = "refund"
    REVERSAL = "reversal"

class TransactionStatus(enum.Enum):
    """Status of banking transactions."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"

class Transaction(BaseModel):
    """
    Transaction model representing all banking transactions.
    """
    __tablename__ = "transactions"
    
    # Transaction identification
    transaction_id = Column(String(30), unique=True, nullable=False, index=True)
    reference_number = Column(String(50), nullable=True, index=True)
    
    # Transaction details
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    description = Column(Text, nullable=True)
    
    # Transaction metadata
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    value_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    
    # Account information
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    
    # Transfer/Payment specific fields
    to_account_number = Column(String(20), nullable=True)
    to_account_name = Column(String(100), nullable=True)
    to_bank_ifsc = Column(String(11), nullable=True)
    
    # System information
    initiated_by = Column(String(50), nullable=True)  # User who initiated
    processed_by = Column(String(50), nullable=True)  # User who processed
    channel = Column(String(20), default="WEB", nullable=False)  # WEB, MOBILE, ATM, BRANCH
    
    # Fees and charges
    fee_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    
    # Balance tracking
    balance_before = Column(Numeric(15, 2), nullable=True)
    balance_after = Column(Numeric(15, 2), nullable=True)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    
    @property
    def amount_inr(self) -> str:
        """Get amount formatted as INR."""
        return f"₹{self.amount:,.2f}"
    
    @property
    def total_amount(self) -> Decimal:
        """Get total amount including fees and taxes."""
        return self.amount + self.fee_amount + self.tax_amount
    
    @property
    def is_credit(self) -> bool:
        """Check if transaction is a credit to the account."""
        return self.transaction_type in [
            TransactionType.DEPOSIT,
            TransactionType.INTEREST_CREDIT,
            TransactionType.REFUND
        ]
    
    @property
    def is_debit(self) -> bool:
        """Check if transaction is a debit from the account."""
        return self.transaction_type in [
            TransactionType.WITHDRAWAL,
            TransactionType.TRANSFER,
            TransactionType.PAYMENT,
            TransactionType.FEE_DEBIT
        ]
    
    @property
    def is_completed(self) -> bool:
        """Check if transaction is completed."""
        return self.status == TransactionStatus.COMPLETED
    
    @property
    def is_pending(self) -> bool:
        """Check if transaction is pending."""
        return self.status in [TransactionStatus.PENDING, TransactionStatus.PROCESSING]
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.transaction_id}, type={self.transaction_type.value}, amount={self.amount}, status={self.status.value})>"
