"""
Transaction Service Domain Entities
Business entities for transaction processing and management
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal
import uuid


class TransactionType(str, Enum):
    """Transaction type enumeration"""
    TRANSFER = "transfer"  # Account to account transfer
    DEPOSIT = "deposit"    # Cash deposit
    WITHDRAWAL = "withdrawal"  # Cash withdrawal
    PAYMENT = "payment"    # Bill payment or merchant payment
    REFUND = "refund"      # Refund transaction
    FEE = "fee"           # Fee deduction
    INTEREST = "interest"  # Interest credit
    REVERSAL = "reversal"  # Transaction reversal


class TransactionStatus(str, Enum):
    """Transaction status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"


class TransactionChannel(str, Enum):
    """Transaction channel enumeration"""
    ATM = "atm"
    ONLINE_BANKING = "online_banking"
    MOBILE_BANKING = "mobile_banking"
    BRANCH = "branch"
    POS = "pos"
    API = "api"
    SYSTEM = "system"


class Priority(str, Enum):
    """Transaction priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Money:
    """Money value object"""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency is required")
        
        # Round to 2 decimal places for currency
        self.amount = self.amount.quantize(Decimal('0.01'))
    
    def add(self, other: 'Money') -> 'Money':
        """Add money amounts"""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """Subtract money amounts"""
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)
    
    def __str__(self) -> str:
        return f"{self.currency} {self.amount}"


@dataclass
class TransactionLeg:
    """Individual leg of a transaction (debit or credit)"""
    leg_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str = ""
    leg_type: str = ""  # "debit" or "credit"
    amount: Money = field(default_factory=lambda: Money(Decimal('0')))
    balance_before: Money = field(default_factory=lambda: Money(Decimal('0')))
    balance_after: Money = field(default_factory=lambda: Money(Decimal('0')))
    description: str = ""
    
    def __post_init__(self):
        if not self.account_id:
            raise ValueError("Account ID is required")
        if self.leg_type not in ["debit", "credit"]:
            raise ValueError("Leg type must be 'debit' or 'credit'")


@dataclass
class Transaction:
    """Transaction aggregate root"""
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    transaction_type: TransactionType = TransactionType.TRANSFER
    status: TransactionStatus = TransactionStatus.PENDING
    priority: Priority = Priority.NORMAL
    
    # Transaction details
    amount: Money = field(default_factory=lambda: Money(Decimal('0')))
    currency: str = "USD"
    description: str = ""
    reference_number: str = ""
    
    # Accounts involved
    from_account_id: Optional[str] = None
    to_account_id: Optional[str] = None
    legs: List[TransactionLeg] = field(default_factory=list)
    
    # Channel and timing
    channel: TransactionChannel = TransactionChannel.SYSTEM
    initiated_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Authorization and audit
    initiated_by: str = ""
    authorized_by: Optional[str] = None
    
    # Error handling
    failure_reason: str = ""
    retry_count: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    
    def __post_init__(self):
        if not self.reference_number:
            self.reference_number = self._generate_reference_number()
    
    def _generate_reference_number(self) -> str:
        """Generate unique reference number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = self.transaction_id[:8].upper()
        return f"TXN{timestamp}{unique_id}"
    
    def complete(self):
        """Mark transaction as completed"""
        self.status = TransactionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def fail(self, reason: str):
        """Mark transaction as failed"""
        self.status = TransactionStatus.FAILED
        self.failure_reason = reason
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def is_completed(self) -> bool:
        """Check if transaction is completed"""
        return self.status == TransactionStatus.COMPLETED
