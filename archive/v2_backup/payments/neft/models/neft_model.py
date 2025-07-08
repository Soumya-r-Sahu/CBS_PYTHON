"""
NEFT Payment Models - Core Banking System

This module defines data models for NEFT payments.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class NEFTStatus(str, Enum):
    """NEFT transaction status enumeration."""
    INITIATED = "INITIATED"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    PENDING_RBI = "PENDING_RBI"  # Waiting for RBI processing
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETURNED = "RETURNED"  # Returned by beneficiary bank
    CANCELLED = "CANCELLED"


class NEFTReturnReason(str, Enum):
    """Standard NEFT return reason codes as per RBI guidelines."""
    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    ACCOUNT_FROZEN = "ACCOUNT_FROZEN"
    INVALID_ACCOUNT = "INVALID_ACCOUNT"
    BENEFICIARY_DECEASED = "BENEFICIARY_DECEASED"
    AMOUNT_EXCEEDS_LIMIT = "AMOUNT_EXCEEDS_LIMIT"
    ACCOUNT_TRANSFERRED = "ACCOUNT_TRANSFERRED"
    INCORRECT_BENEFICIARY = "INCORRECT_BENEFICIARY"
    OTHER = "OTHER"


@dataclass
class NEFTPaymentDetails:
    """Detailed information for NEFT payment."""
    sender_account_number: str
    sender_ifsc_code: str
    sender_account_type: str
    sender_name: str
    beneficiary_account_number: str
    beneficiary_ifsc_code: str
    beneficiary_account_type: str
    beneficiary_name: str
    amount: float
    payment_reference: str
    remarks: Optional[str] = None


@dataclass
class NEFTTransaction:
    """NEFT Transaction model."""
    transaction_id: str
    utr_number: Optional[str] = None  # Unique Transaction Reference number (assigned by system)
    payment_details: NEFTPaymentDetails = field(default_factory=NEFTPaymentDetails)
    status: NEFTStatus = NEFTStatus.INITIATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    batch_number: Optional[str] = None  # NEFT transactions are processed in batches
    return_reason: Optional[NEFTReturnReason] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_status(self, new_status: NEFTStatus):
        """Update status and related timestamps."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if new_status == NEFTStatus.PROCESSING:
            self.processed_at = datetime.utcnow()
        elif new_status in [NEFTStatus.COMPLETED, NEFTStatus.FAILED, NEFTStatus.RETURNED]:
            self.completed_at = datetime.utcnow()
    
    def is_completed(self) -> bool:
        """Check if transaction is completed (successfully or not)."""
        return self.status in [NEFTStatus.COMPLETED, NEFTStatus.FAILED, NEFTStatus.RETURNED, NEFTStatus.CANCELLED]
    
    def is_successful(self) -> bool:
        """Check if transaction completed successfully."""
        return self.status == NEFTStatus.COMPLETED


@dataclass
class NEFTBatch:
    """NEFT Batch model - NEFT transactions are processed in time-based batches."""
    batch_id: str
    batch_time: datetime
    total_transactions: int = 0
    total_amount: float = 0.0
    completed_transactions: int = 0
    failed_transactions: int = 0
    status: str = "PENDING"
    transactions: List[str] = field(default_factory=list)  # List of transaction IDs
