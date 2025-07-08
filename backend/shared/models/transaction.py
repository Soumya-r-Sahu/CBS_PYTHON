"""
Transaction Model for Core Banking System V3.0
"""

from sqlalchemy import Column, String, Numeric, ForeignKey, Enum, DateTime, Text
from sqlalchemy.orm import relationship
from decimal import Decimal
import enum

from .base import BaseModel

class TransactionType(enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    INTEREST_CREDIT = "INTEREST_CREDIT"
    FEE_DEBIT = "FEE_DEBIT"
    REVERSAL = "REVERSAL"

class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REVERSED = "REVERSED"

class TransactionChannel(enum.Enum):
    ATM = "ATM"
    BRANCH = "BRANCH"
    ONLINE = "ONLINE"
    MOBILE = "MOBILE"
    POS = "POS"
    UPI = "UPI"
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"

class Transaction(BaseModel):
    """Transaction model for all banking transactions"""
    __tablename__ = "transactions"
    
    # Transaction Information
    transaction_id = Column(String(30), unique=True, nullable=False)  # TXN-YYYYMMDD-XXXXX
    reference_number = Column(String(50), unique=True)
    
    # Account Reference
    account_id = Column(ForeignKey("accounts.id"), nullable=False)
    
    # Transaction Details
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    
    # Balance Information
    balance_before = Column(Numeric(15, 2), nullable=False)
    balance_after = Column(Numeric(15, 2), nullable=False)
    
    # Transaction Status
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    channel = Column(Enum(TransactionChannel), nullable=False)
    
    # Description and Notes
    description = Column(String(200), nullable=False)
    notes = Column(Text)
    
    # Transfer Information (for transfers)
    to_account_id = Column(ForeignKey("accounts.id"))
    to_account_number = Column(String(20))
    to_beneficiary_name = Column(String(100))
    to_ifsc_code = Column(String(11))
    
    # Processing Information
    processed_at = Column(DateTime)
    processed_by = Column(String(50))  # User ID or system
    
    # Error Information
    error_code = Column(String(20))
    error_message = Column(String(500))
    
    # Relationships
    account = relationship("Account", back_populates="transactions", foreign_keys=[account_id])
    to_account = relationship("Account", foreign_keys=[to_account_id])
    
    def is_successful(self) -> bool:
        """Check if transaction is successful"""
        return self.status == TransactionStatus.COMPLETED
    
    def is_pending(self) -> bool:
        """Check if transaction is pending"""
        return self.status in [TransactionStatus.PENDING, TransactionStatus.PROCESSING]
    
    def can_be_reversed(self) -> bool:
        """Check if transaction can be reversed"""
        return self.status == TransactionStatus.COMPLETED and self.transaction_type != TransactionType.REVERSAL
    
    def get_transaction_summary(self):
        """Get transaction summary"""
        return {
            'transaction_id': self.transaction_id,
            'type': self.transaction_type.value,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status.value,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
