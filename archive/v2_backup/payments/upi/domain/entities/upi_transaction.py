"""
UPI Transaction entity in the domain layer.
This entity represents a UPI transaction with all business rules applied.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class UpiTransactionStatus(Enum):
    """Enum representing the possible statuses of a UPI transaction."""
    INITIATED = "initiated"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    REVERSED = "reversed"


@dataclass
class UpiTransaction:
    """UPI Transaction entity that encapsulates the business rules for UPI transactions."""
    
    # Required fields
    transaction_id: UUID
    sender_vpa: str
    receiver_vpa: str
    amount: float
    transaction_date: datetime
    status: UpiTransactionStatus
    
    # Optional fields
    remarks: Optional[str] = None
    reference_id: Optional[str] = None
    failure_reason: Optional[str] = None
    
    @classmethod
    def create(cls, sender_vpa: str, receiver_vpa: str, amount: float, 
               remarks: Optional[str] = None) -> 'UpiTransaction':
        """Factory method to create a new UPI transaction."""
        if amount <= 0:
            raise ValueError("Transaction amount must be greater than zero")
        
        if not sender_vpa or not receiver_vpa:
            raise ValueError("Sender and receiver VPA must be provided")
        
        return cls(
            transaction_id=uuid4(),
            sender_vpa=sender_vpa,
            receiver_vpa=receiver_vpa,
            amount=amount,
            remarks=remarks,
            transaction_date=datetime.now(),
            status=UpiTransactionStatus.INITIATED
        )
    
    def complete(self, reference_id: str) -> None:
        """Mark the transaction as completed with a reference ID."""
        if self.status not in [UpiTransactionStatus.INITIATED, UpiTransactionStatus.PENDING]:
            raise ValueError(f"Cannot complete transaction with status: {self.status}")
        
        self.status = UpiTransactionStatus.COMPLETED
        self.reference_id = reference_id
    
    def fail(self, reason: str) -> None:
        """Mark the transaction as failed with a reason."""
        if self.status not in [UpiTransactionStatus.INITIATED, UpiTransactionStatus.PENDING]:
            raise ValueError(f"Cannot fail transaction with status: {self.status}")
        
        self.status = UpiTransactionStatus.FAILED
        self.failure_reason = reason
    
    def reject(self, reason: str) -> None:
        """Mark the transaction as rejected with a reason."""
        if self.status != UpiTransactionStatus.INITIATED:
            raise ValueError(f"Cannot reject transaction with status: {self.status}")
        
        self.status = UpiTransactionStatus.REJECTED
        self.failure_reason = reason
    
    def reverse(self, reason: str) -> None:
        """Mark the transaction as reversed with a reason."""
        if self.status != UpiTransactionStatus.COMPLETED:
            raise ValueError(f"Cannot reverse transaction with status: {self.status}")
        
        self.status = UpiTransactionStatus.REVERSED
        self.failure_reason = reason
