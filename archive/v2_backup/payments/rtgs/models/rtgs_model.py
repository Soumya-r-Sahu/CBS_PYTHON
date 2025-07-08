"""
RTGS Payment Models - Core Banking System

This module defines data models for RTGS payments.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class RTGSStatus(str, Enum):
    """RTGS transaction status enumeration."""
    INITIATED = "INITIATED"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    PENDING_RBI = "PENDING_RBI"  # Waiting for RBI processing
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETURNED = "RETURNED"  # Returned by beneficiary bank
    CANCELLED = "CANCELLED"


class RTGSReturnReason(str, Enum):
    """Standard RTGS return reason codes as per RBI guidelines."""
    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    ACCOUNT_FROZEN = "ACCOUNT_FROZEN"
    INVALID_ACCOUNT = "INVALID_ACCOUNT"
    BENEFICIARY_DECEASED = "BENEFICIARY_DECEASED"
    AMOUNT_BELOW_LIMIT = "AMOUNT_BELOW_LIMIT"  # RTGS has minimum amount limits
    ACCOUNT_TRANSFERRED = "ACCOUNT_TRANSFERRED"
    INCORRECT_BENEFICIARY = "INCORRECT_BENEFICIARY"
    OTHER = "OTHER"


@dataclass
class RTGSPaymentDetails:
    """Detailed information for RTGS payment."""
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
    purpose_code: Optional[str] = None  # Purpose code as per RBI guidelines for RTGS


@dataclass
class RTGSTransaction:
    """RTGS Transaction model."""
    transaction_id: str
    utr_number: Optional[str] = None  # Unique Transaction Reference number (assigned by system)
    payment_details: RTGSPaymentDetails = field(default_factory=RTGSPaymentDetails)
    status: RTGSStatus = RTGSStatus.INITIATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    return_reason: Optional[RTGSReturnReason] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_status(self, new_status: RTGSStatus):
        """Update status and related timestamps."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if new_status == RTGSStatus.PROCESSING:
            self.processed_at = datetime.utcnow()
        elif new_status in [RTGSStatus.COMPLETED, RTGSStatus.FAILED, RTGSStatus.RETURNED]:
            self.completed_at = datetime.utcnow()
    
    def is_completed(self) -> bool:
        """Check if transaction is completed (successfully or not)."""
        return self.status in [RTGSStatus.COMPLETED, RTGSStatus.FAILED, RTGSStatus.RETURNED, RTGSStatus.CANCELLED]
    
    def is_successful(self) -> bool:
        """Check if transaction completed successfully."""
        return self.status == RTGSStatus.COMPLETED
