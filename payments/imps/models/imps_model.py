"""
IMPS Payment Models - Core Banking System

This module defines data models for IMPS payments.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class IMPSStatus(str, Enum):
    """IMPS transaction status enumeration."""
    INITIATED = "INITIATED"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    PENDING = "PENDING"  # Waiting for NPCI response
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"  # Transaction reversed
    CANCELLED = "CANCELLED"


class IMPSReturnReason(str, Enum):
    """Standard IMPS return reason codes as per NPCI guidelines."""
    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    ACCOUNT_FROZEN = "ACCOUNT_FROZEN"
    ACCOUNT_DOES_NOT_EXIST = "ACCOUNT_DOES_NOT_EXIST"
    BENEFICIARY_BANK_NOT_AVAILABLE = "BENEFICIARY_BANK_NOT_AVAILABLE"
    CREDIT_LIMIT_EXCEEDED = "CREDIT_LIMIT_EXCEEDED"
    DUPLICATE_TRANSACTION = "DUPLICATE_TRANSACTION"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    INVALID_ACCOUNT = "INVALID_ACCOUNT"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    INVALID_BENEFICIARY = "INVALID_BENEFICIARY"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    TIMEOUT = "TIMEOUT"
    OTHER = "OTHER"


class IMPSType(str, Enum):
    """IMPS transaction type."""
    P2P = "P2P"  # Person to Person
    P2A = "P2A"  # Person to Account
    P2M = "P2M"  # Person to Merchant
    BULK = "BULK"  # Bulk Payment


class IMPSChannel(str, Enum):
    """Channel through which IMPS was initiated."""
    MOBILE = "MOBILE"
    INTERNET = "INTERNET"
    BRANCH = "BRANCH"
    ATM = "ATM"
    CALL_CENTER = "CALL_CENTER"
    API = "API"


@dataclass
class IMPSPaymentDetails:
    """Detailed information for IMPS payment."""
    sender_account_number: str
    sender_ifsc_code: str
    sender_mobile_number: Optional[str] = None
    sender_mmid: Optional[str] = None  # Mobile Money Identifier
    sender_name: str
    beneficiary_account_number: str
    beneficiary_ifsc_code: str
    beneficiary_mobile_number: Optional[str] = None
    beneficiary_mmid: Optional[str] = None
    beneficiary_name: str
    amount: float
    reference_number: str  # Transaction reference number
    remarks: Optional[str] = None
    imps_type: IMPSType = IMPSType.P2A
    channel: IMPSChannel = IMPSChannel.API


@dataclass
class IMPSTransaction:
    """IMPS Transaction model."""
    transaction_id: str
    rrn: Optional[str] = None  # RRN (Reference Retrieval Number) assigned by NPCI
    payment_details: IMPSPaymentDetails = field(default_factory=IMPSPaymentDetails)
    status: IMPSStatus = IMPSStatus.INITIATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    return_reason: Optional[IMPSReturnReason] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_status(self, new_status: IMPSStatus):
        """Update status and related timestamps."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if new_status == IMPSStatus.PROCESSING:
            self.processed_at = datetime.utcnow()
        elif new_status in [IMPSStatus.COMPLETED, IMPSStatus.FAILED, IMPSStatus.REVERSED]:
            self.completed_at = datetime.utcnow()
    
    def is_completed(self) -> bool:
        """Check if transaction is completed (successfully or not)."""
        return self.status in [IMPSStatus.COMPLETED, IMPSStatus.FAILED, IMPSStatus.REVERSED, IMPSStatus.CANCELLED]
    
    def is_successful(self) -> bool:
        """Check if transaction completed successfully."""
        return self.status == IMPSStatus.COMPLETED
