"""
Transaction Domain Entities

Core business entities for transaction management in CBS platform.
Implements rich domain models with business logic encapsulation.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from platform.shared.events import DomainEvent


class TransactionType(Enum):
    """Transaction types supported by the platform."""
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT = "DEPOSIT"
    INTEREST = "INTEREST"
    FEE = "FEE"
    REVERSAL = "REVERSAL"


class TransactionStatus(Enum):
    """Transaction processing status."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REVERSED = "REVERSED"


class TransactionChannel(Enum):
    """Channel through which transaction was initiated."""
    BRANCH = "BRANCH"
    ATM = "ATM"
    ONLINE = "ONLINE"
    MOBILE = "MOBILE"
    API = "API"
    INTERNAL = "INTERNAL"


@dataclass(frozen=True)
class Money:
    """Value object representing monetary amount."""
    amount: Decimal
    currency: str = "INR"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency is required")
    
    def add(self, other: 'Money') -> 'Money':
        """Add two money amounts."""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """Subtract money amount."""
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)


@dataclass
class TransactionLeg:
    """Individual leg of a transaction (debit or credit)."""
    account_id: UUID
    amount: Money
    transaction_type: TransactionType
    description: str
    reference: Optional[str] = None
    
    def is_debit(self) -> bool:
        """Check if this leg is a debit."""
        return self.transaction_type in [
            TransactionType.DEBIT, 
            TransactionType.WITHDRAWAL, 
            TransactionType.PAYMENT
        ]
    
    def is_credit(self) -> bool:
        """Check if this leg is a credit."""
        return self.transaction_type in [
            TransactionType.CREDIT, 
            TransactionType.DEPOSIT
        ]


@dataclass
class TransactionMetadata:
    """Additional transaction metadata."""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None
    location: Optional[str] = None
    additional_data: dict = field(default_factory=dict)


class Transaction:
    """
    Transaction aggregate root.
    
    Represents a complete financial transaction with proper
    double-entry bookkeeping and business rules.
    """
    
    def __init__(
        self,
        transaction_id: Optional[UUID] = None,
        reference_number: Optional[str] = None,
        customer_id: Optional[UUID] = None
    ):
        self.transaction_id = transaction_id or uuid4()
        self.reference_number = reference_number or self._generate_reference()
        self.customer_id = customer_id
        self.legs: List[TransactionLeg] = []
        self.status = TransactionStatus.PENDING
        self.channel = TransactionChannel.INTERNAL
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata = TransactionMetadata()
        self.events: List[DomainEvent] = []
        self.authorized_by: Optional[UUID] = None
        self.settlement_date: Optional[datetime] = None
        self.error_message: Optional[str] = None
        
    def add_leg(self, leg: TransactionLeg) -> None:
        """Add a transaction leg."""
        self.legs.append(leg)
        self.updated_at = datetime.utcnow()
    
    def add_debit_leg(
        self, 
        account_id: UUID, 
        amount: Money, 
        description: str,
        reference: Optional[str] = None
    ) -> None:
        """Add a debit leg to the transaction."""
        leg = TransactionLeg(
            account_id=account_id,
            amount=amount,
            transaction_type=TransactionType.DEBIT,
            description=description,
            reference=reference
        )
        self.add_leg(leg)
    
    def add_credit_leg(
        self, 
        account_id: UUID, 
        amount: Money, 
        description: str,
        reference: Optional[str] = None
    ) -> None:
        """Add a credit leg to the transaction."""
        leg = TransactionLeg(
            account_id=account_id,
            amount=amount,
            transaction_type=TransactionType.CREDIT,
            description=description,
            reference=reference
        )
        self.add_leg(leg)
    
    def is_balanced(self) -> bool:
        """Check if transaction is balanced (debits = credits)."""
        debit_total = sum(
            leg.amount.amount for leg in self.legs 
            if leg.is_debit()
        )
        credit_total = sum(
            leg.amount.amount for leg in self.legs 
            if leg.is_credit()
        )
        return debit_total == credit_total
    
    def validate(self) -> List[str]:
        """Validate transaction business rules."""
        errors = []
        
        if not self.legs:
            errors.append("Transaction must have at least one leg")
        
        if len(self.legs) < 2:
            errors.append("Transaction must have at least two legs")
        
        if not self.is_balanced():
            errors.append("Transaction must be balanced (debits = credits)")
        
        # Check for duplicate account legs of same type
        account_type_pairs = [(leg.account_id, leg.transaction_type) for leg in self.legs]
        if len(account_type_pairs) != len(set(account_type_pairs)):
            errors.append("Duplicate account-type combinations not allowed")
        
        return errors
    
    def authorize(self, authorized_by: UUID) -> None:
        """Authorize the transaction."""
        if self.status != TransactionStatus.PENDING:
            raise ValueError("Can only authorize pending transactions")
        
        validation_errors = self.validate()
        if validation_errors:
            raise ValueError(f"Transaction validation failed: {validation_errors}")
        
        self.authorized_by = authorized_by
        self.status = TransactionStatus.PROCESSING
        self.updated_at = datetime.utcnow()
        
        # Emit domain event
        event = TransactionAuthorized(
            transaction_id=self.transaction_id,
            reference_number=self.reference_number,
            authorized_by=authorized_by,
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
    
    def complete(self, settlement_date: Optional[datetime] = None) -> None:
        """Mark transaction as completed."""
        if self.status != TransactionStatus.PROCESSING:
            raise ValueError("Can only complete processing transactions")
        
        self.status = TransactionStatus.COMPLETED
        self.settlement_date = settlement_date or datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Emit domain event
        event = TransactionCompleted(
            transaction_id=self.transaction_id,
            reference_number=self.reference_number,
            settlement_date=self.settlement_date,
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
    
    def fail(self, error_message: str) -> None:
        """Mark transaction as failed."""
        if self.status not in [TransactionStatus.PENDING, TransactionStatus.PROCESSING]:
            raise ValueError("Can only fail pending or processing transactions")
        
        self.status = TransactionStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
        
        # Emit domain event
        event = TransactionFailed(
            transaction_id=self.transaction_id,
            reference_number=self.reference_number,
            error_message=error_message,
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
    
    def reverse(self, reversed_by: UUID, reason: str) -> 'Transaction':
        """Create a reversal transaction."""
        if self.status != TransactionStatus.COMPLETED:
            raise ValueError("Can only reverse completed transactions")
        
        # Create reversal transaction
        reversal = Transaction(
            customer_id=self.customer_id
        )
        reversal.channel = self.channel
        reversal.metadata = self.metadata
        
        # Add reversed legs
        for leg in self.legs:
            reversed_type = (
                TransactionType.CREDIT if leg.is_debit() 
                else TransactionType.DEBIT
            )
            reversed_leg = TransactionLeg(
                account_id=leg.account_id,
                amount=leg.amount,
                transaction_type=reversed_type,
                description=f"Reversal: {leg.description}",
                reference=f"REV-{self.reference_number}"
            )
            reversal.add_leg(reversed_leg)
        
        # Emit domain event
        event = TransactionReversed(
            original_transaction_id=self.transaction_id,
            reversal_transaction_id=reversal.transaction_id,
            reversed_by=reversed_by,
            reason=reason,
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
        
        return reversal
    
    def _generate_reference(self) -> str:
        """Generate unique transaction reference number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"TXN{timestamp}{str(self.transaction_id)[:8].upper()}"


# Domain Events
@dataclass(frozen=True)
class TransactionAuthorized(DomainEvent):
    """Event emitted when transaction is authorized."""
    transaction_id: UUID
    reference_number: str
    authorized_by: UUID


@dataclass(frozen=True)
class TransactionCompleted(DomainEvent):
    """Event emitted when transaction is completed."""
    transaction_id: UUID
    reference_number: str
    settlement_date: datetime


@dataclass(frozen=True)
class TransactionFailed(DomainEvent):
    """Event emitted when transaction fails."""
    transaction_id: UUID
    reference_number: str
    error_message: str


@dataclass(frozen=True)
class TransactionReversed(DomainEvent):
    """Event emitted when transaction is reversed."""
    original_transaction_id: UUID
    reversal_transaction_id: UUID
    reversed_by: UUID
    reason: str


# Export public interface
__all__ = [
    "Transaction",
    "TransactionLeg", 
    "TransactionType",
    "TransactionStatus",
    "TransactionChannel",
    "TransactionMetadata",
    "Money",
    "TransactionAuthorized",
    "TransactionCompleted", 
    "TransactionFailed",
    "TransactionReversed"
]
