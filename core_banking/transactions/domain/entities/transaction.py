"""
Transaction Entity Module

This module defines the Transaction entity and related value objects for the Core Banking System.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path


class TransactionStatus(Enum):
    """Transaction status values"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"

class TransactionType(Enum):
    """Transaction type values"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    REVERSAL = "reversal"
    PAYMENT = "payment"
    REFUND = "refund"
    CHARGE = "charge"
    INTEREST = "interest"

class TransactionMetadata:
    """Value object for transaction metadata"""
    
    def __init__(self, 
                 channel: str = "SYSTEM", 
                 location: Optional[str] = None,
                 device_id: Optional[str] = None,
                 ip_address: Optional[str] = None,
                 user_agent: Optional[str] = None,
                 reference_id: Optional[str] = None,
                 tags: Optional[Dict[str, str]] = None):
        self.channel = channel
        self.location = location
        self.device_id = device_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.reference_id = reference_id
        self.tags = tags or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "channel": self.channel,
            "location": self.location,
            "device_id": self.device_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "reference_id": self.reference_id,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransactionMetadata':
        """Create from dictionary"""
        return cls(
            channel=data.get("channel", "SYSTEM"),
            location=data.get("location"),
            device_id=data.get("device_id"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            reference_id=data.get("reference_id"),
            tags=data.get("tags", {})
        )

class Transaction:
    """
    Transaction entity for the Core Banking System.
    
    Represents a financial transaction in the banking system.
    Follows immutability principles for core fields with controlled state transitions.
    """
    
    def __init__(self,
                 transaction_id: Optional[UUID] = None,
                 account_id: UUID = None,
                 amount: Decimal = Decimal('0'),
                 transaction_type: TransactionType = None,
                 status: TransactionStatus = TransactionStatus.PENDING,
                 description: str = "",
                 timestamp: datetime = None,
                 metadata: Optional[TransactionMetadata] = None,
                 reference_transaction_id: Optional[UUID] = None,
                 to_account_id: Optional[UUID] = None):
        """
        Initialize a new Transaction.
        
        Args:
            transaction_id: Unique identifier (generated if not provided)
            account_id: Source account ID
            amount: Transaction amount
            transaction_type: Type of transaction (deposit, withdrawal, etc.)
            status: Current status (default: PENDING)
            description: User-friendly description
            timestamp: When the transaction occurred (defaults to now)
            metadata: Additional transaction metadata
            reference_transaction_id: ID of a related transaction (for reversals, etc.)
            to_account_id: Target account ID (for transfers)
        """
        # Core immutable attributes
        self._transaction_id = transaction_id or uuid4()
        self._account_id = account_id
        self._amount = Decimal(str(amount))
        self._transaction_type = transaction_type
        self._timestamp = timestamp or datetime.now()
        self._reference_transaction_id = reference_transaction_id
        self._to_account_id = to_account_id
        
        # Mutable attributes
        self._status = status
        self._description = description
        self._metadata = metadata or TransactionMetadata()
        self._completed_at = None
        self._failure_reason = None
    
    @property
    def transaction_id(self) -> UUID:
        """Get transaction ID"""
        return self._transaction_id
    
    @property
    def account_id(self) -> UUID:
        """Get account ID"""
        return self._account_id
    
    @property
    def amount(self) -> Decimal:
        """Get transaction amount"""
        return self._amount
    
    @property
    def transaction_type(self) -> TransactionType:
        """Get transaction type"""
        return self._transaction_type
    
    @property
    def status(self) -> TransactionStatus:
        """Get current status"""
        return self._status
    
    @property
    def description(self) -> str:
        """Get description"""
        return self._description
    
    @property
    def timestamp(self) -> datetime:
        """Get creation timestamp"""
        return self._timestamp
    
    @property
    def metadata(self) -> TransactionMetadata:
        """Get metadata"""
        return self._metadata
    
    @property
    def reference_transaction_id(self) -> Optional[UUID]:
        """Get reference transaction ID"""
        return self._reference_transaction_id
    
    @property
    def to_account_id(self) -> Optional[UUID]:
        """Get target account ID for transfers"""
        return self._to_account_id
    
    @property
    def completed_at(self) -> Optional[datetime]:
        """Get completion timestamp"""
        return self._completed_at
    
    @property
    def failure_reason(self) -> Optional[str]:
        """Get failure reason if failed"""
        return self._failure_reason
    
    def complete(self) -> 'Transaction':
        """Mark transaction as completed"""
        if self._status != TransactionStatus.PENDING:
            raise ValueError(f"Cannot complete transaction in {self._status.value} state")
        
        self._status = TransactionStatus.COMPLETED
        self._completed_at = datetime.now()
        return self
    
    def fail(self, reason: str) -> 'Transaction':
        """Mark transaction as failed with reason"""
        if self._status != TransactionStatus.PENDING:
            raise ValueError(f"Cannot fail transaction in {self._status.value} state")
        
        self._status = TransactionStatus.FAILED
        self._failure_reason = reason
        return self
    
    def reverse(self) -> 'Transaction':
        """Mark transaction as reversed"""
        if self._status != TransactionStatus.COMPLETED:
            raise ValueError(f"Cannot reverse transaction in {self._status.value} state")
        
        self._status = TransactionStatus.REVERSED
        return self
    
    def update_description(self, description: str) -> 'Transaction':
        """Update transaction description"""
        self._description = description
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "transaction_id": str(self._transaction_id),
            "account_id": str(self._account_id) if self._account_id else None,
            "amount": str(self._amount),
            "transaction_type": self._transaction_type.value if self._transaction_type else None,
            "status": self._status.value,
            "description": self._description,
            "timestamp": self._timestamp.isoformat(),
            "metadata": self._metadata.to_dict(),
            "reference_transaction_id": str(self._reference_transaction_id) if self._reference_transaction_id else None,
            "to_account_id": str(self._to_account_id) if self._to_account_id else None,
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "failure_reason": self._failure_reason
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create from dictionary"""
        return cls(
            transaction_id=UUID(data["transaction_id"]) if data.get("transaction_id") else None,
            account_id=UUID(data["account_id"]) if data.get("account_id") else None,
            amount=Decimal(data["amount"]) if data.get("amount") else Decimal('0'),
            transaction_type=TransactionType(data["transaction_type"]) if data.get("transaction_type") else None,
            status=TransactionStatus(data["status"]) if data.get("status") else TransactionStatus.PENDING,
            description=data.get("description", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            metadata=TransactionMetadata.from_dict(data["metadata"]) if data.get("metadata") else None,
            reference_transaction_id=UUID(data["reference_transaction_id"]) if data.get("reference_transaction_id") else None,
            to_account_id=UUID(data["to_account_id"]) if data.get("to_account_id") else None
        )
    
    def __str__(self) -> str:
        """String representation"""
        return f"Transaction {self._transaction_id}: {self._amount} ({self._transaction_type.value if self._transaction_type else 'unknown'}) - {self._status.value}"
