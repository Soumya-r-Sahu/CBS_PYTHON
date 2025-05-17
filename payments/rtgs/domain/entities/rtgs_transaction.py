"""
RTGS Transaction entity in the domain layer.
This entity represents a RTGS transaction with all business rules applied.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4


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
    AMOUNT_BELOW_THRESHOLD = "AMOUNT_BELOW_THRESHOLD"
    ACCOUNT_TRANSFERRED = "ACCOUNT_TRANSFERRED"
    INCORRECT_BENEFICIARY = "INCORRECT_BENEFICIARY"
    OTHER = "OTHER"


class RTGSPriority(str, Enum):
    """RTGS transaction priority enumeration."""
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


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
    priority: RTGSPriority = RTGSPriority.NORMAL
    
    def validate(self) -> bool:
        """
        Validate payment details.
        
        Returns:
            bool: True if valid, raises ValueError otherwise
        """
        if not self.sender_account_number or len(self.sender_account_number) < 5:
            raise ValueError("Invalid sender account number")
            
        if not self.sender_ifsc_code or len(self.sender_ifsc_code) != 11:
            raise ValueError("Invalid sender IFSC code")
            
        if not self.beneficiary_account_number or len(self.beneficiary_account_number) < 5:
            raise ValueError("Invalid beneficiary account number")
            
        if not self.beneficiary_ifsc_code or len(self.beneficiary_ifsc_code) != 11:
            raise ValueError("Invalid beneficiary IFSC code")
            
        if self.amount <= 200000:  # RTGS minimum threshold is 2 lakhs
            raise ValueError("Amount must be greater than 2 lakhs for RTGS transfers")
            
        if not self.sender_name or not self.beneficiary_name:
            raise ValueError("Sender and beneficiary names are required")
            
        return True


@dataclass
class RTGSTransaction:
    """RTGS Transaction entity that encapsulates the business rules for RTGS transactions."""
    
    # Required fields
    id: UUID = field(default_factory=uuid4)
    payment_details: RTGSPaymentDetails = field(default_factory=RTGSPaymentDetails)
    
    # System-populated fields
    transaction_reference: str = ""  # Bank-generated reference
    utr_number: Optional[str] = None  # Unique Transaction Reference number (assigned by RBI)
    status: RTGSStatus = RTGSStatus.INITIATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    return_reason: Optional[RTGSReturnReason] = None
    error_message: Optional[str] = None
    customer_id: Optional[str] = None  # Optional link to customer
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls, 
        payment_details: RTGSPaymentDetails,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'RTGSTransaction':
        """
        Factory method to create a new RTGS transaction.
        
        Args:
            payment_details: The payment details
            customer_id: Optional customer ID
            metadata: Additional metadata
            
        Returns:
            A new RTGSTransaction
        """
        # Validate payment details
        payment_details.validate()
        
        # Generate a transaction reference
        now = datetime.utcnow()
        reference = f"RTGS{now.strftime('%Y%m%d%H%M%S')}{str(uuid4())[:8]}"
        
        return cls(
            payment_details=payment_details,
            transaction_reference=reference,
            customer_id=customer_id,
            metadata=metadata or {}
        )
    
    def update_status(self, new_status: RTGSStatus, error_message: Optional[str] = None):
        """
        Update status and related timestamps.
        
        Args:
            new_status: The new status
            error_message: Optional error message
        """
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if new_status == RTGSStatus.PROCESSING:
            self.processed_at = datetime.utcnow()
        elif new_status in [RTGSStatus.COMPLETED, RTGSStatus.FAILED, RTGSStatus.RETURNED, RTGSStatus.CANCELLED]:
            self.completed_at = datetime.utcnow()
            
        if error_message:
            self.error_message = error_message
    
    def set_return_reason(self, reason: RTGSReturnReason, details: Optional[str] = None):
        """
        Set the return reason when a transaction is returned by the beneficiary bank.
        
        Args:
            reason: The return reason code
            details: Optional additional details
        """
        self.return_reason = reason
        self.update_status(RTGSStatus.RETURNED, details)
    
    def submit_to_rbi(self):
        """Mark the transaction as submitted to RBI."""
        self.update_status(RTGSStatus.PENDING_RBI)
    
    def complete(self, utr_number: str):
        """
        Mark the transaction as completed with a UTR number.
        
        Args:
            utr_number: The UTR number assigned by RBI
        """
        self.utr_number = utr_number
        self.update_status(RTGSStatus.COMPLETED)
    
    def fail(self, reason: str):
        """
        Mark the transaction as failed with a reason.
        
        Args:
            reason: The failure reason
        """
        self.update_status(RTGSStatus.FAILED, reason)
    
    def cancel(self, reason: str):
        """
        Mark the transaction as cancelled with a reason.
        
        Args:
            reason: The cancellation reason
        """
        if self.status in [RTGSStatus.COMPLETED, RTGSStatus.FAILED, RTGSStatus.RETURNED]:
            raise ValueError(f"Cannot cancel transaction with status: {self.status}")
            
        self.update_status(RTGSStatus.CANCELLED, reason)
    
    def is_completed(self) -> bool:
        """
        Check if transaction is completed (successfully or not).
        
        Returns:
            True if completed
        """
        return self.status in [RTGSStatus.COMPLETED, RTGSStatus.FAILED, RTGSStatus.RETURNED, RTGSStatus.CANCELLED]
    
    def is_successful(self) -> bool:
        """
        Check if transaction completed successfully.
        
        Returns:
            True if successful
        """
        return self.status == RTGSStatus.COMPLETED
