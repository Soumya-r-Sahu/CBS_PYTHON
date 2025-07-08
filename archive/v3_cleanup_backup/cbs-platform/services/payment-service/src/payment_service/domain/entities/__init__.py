"""
Payment Domain Entities
Business entities representing payment processing
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal
import uuid


class PaymentType(str, Enum):
    """Payment type enumeration"""
    UPI = "upi"
    NEFT = "neft"
    RTGS = "rtgs"
    IMPS = "imps"
    INTERNAL_TRANSFER = "internal_transfer"
    BILL_PAYMENT = "bill_payment"
    MERCHANT_PAYMENT = "merchant_payment"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    INITIATED = "initiated"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentChannel(str, Enum):
    """Payment channel enumeration"""
    MOBILE = "mobile"
    INTERNET_BANKING = "internet_banking"
    ATM = "atm"
    BRANCH = "branch"
    API = "api"


class FraudRiskLevel(str, Enum):
    """Fraud risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PaymentAmount:
    """Payment amount value object"""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Payment amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency is required")
        
        # Round to 2 decimal places for currency
        self.amount = self.amount.quantize(Decimal('0.01'))
    
    def __str__(self) -> str:
        return f"{self.currency} {self.amount}"


@dataclass
class PaymentParty:
    """Payment party (sender/receiver) value object"""
    account_number: str
    account_name: str
    bank_code: str
    bank_name: str
    branch_code: Optional[str] = None
    ifsc_code: Optional[str] = None
    
    def __post_init__(self):
        if not self.account_number:
            raise ValueError("Account number is required")
        if not self.account_name:
            raise ValueError("Account name is required")


@dataclass
class UPIDetails:
    """UPI-specific payment details"""
    vpa: str  # Virtual Payment Address
    merchant_id: Optional[str] = None
    qr_code: Optional[str] = None
    purpose: str = "PAYMENT"
    
    def __post_init__(self):
        if not self.vpa:
            raise ValueError("VPA is required for UPI payments")
        if '@' not in self.vpa:
            raise ValueError("Invalid VPA format")


@dataclass
class BillPaymentDetails:
    """Bill payment specific details"""
    biller_id: str
    biller_name: str
    bill_number: str
    due_date: Optional[datetime] = None
    bill_amount: Optional[PaymentAmount] = None
    
    def __post_init__(self):
        if not self.biller_id:
            raise ValueError("Biller ID is required")
        if not self.bill_number:
            raise ValueError("Bill number is required")


@dataclass
class FraudCheck:
    """Fraud detection result"""
    risk_level: FraudRiskLevel
    risk_score: int  # 0-100
    flags: List[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not 0 <= self.risk_score <= 100:
            raise ValueError("Risk score must be between 0 and 100")
    
    def is_high_risk(self) -> bool:
        """Check if payment is high risk"""
        return self.risk_level in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]
    
    def requires_approval(self) -> bool:
        """Check if payment requires manual approval"""
        return self.risk_score >= 80 or self.risk_level == FraudRiskLevel.CRITICAL


@dataclass
class Payment:
    """Payment aggregate root"""
    payment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payment_type: PaymentType = PaymentType.INTERNAL_TRANSFER
    amount: PaymentAmount = field(default_factory=lambda: PaymentAmount(Decimal('0')))
    sender: PaymentParty = None
    receiver: PaymentParty = None
    status: PaymentStatus = PaymentStatus.INITIATED
    channel: PaymentChannel = PaymentChannel.API
    reference_number: str = ""
    description: str = ""
    
    # UPI specific
    upi_details: Optional[UPIDetails] = None
    
    # Bill payment specific
    bill_details: Optional[BillPaymentDetails] = None
    
    # Fraud detection
    fraud_check: Optional[FraudCheck] = None
    
    # Timestamps
    initiated_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # System fields
    initiated_by: Optional[str] = None
    processed_by: Optional[str] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    
    def __post_init__(self):
        if not self.sender:
            raise ValueError("Sender is required")
        if not self.receiver:
            raise ValueError("Receiver is required")
        if not self.reference_number:
            self.reference_number = self._generate_reference_number()
        
        # Validate payment type specific details
        if self.payment_type == PaymentType.UPI and not self.upi_details:
            raise ValueError("UPI details are required for UPI payments")
        if self.payment_type == PaymentType.BILL_PAYMENT and not self.bill_details:
            raise ValueError("Bill details are required for bill payments")
    
    def _generate_reference_number(self) -> str:
        """Generate unique reference number"""
        prefix_map = {
            PaymentType.UPI: "UPI",
            PaymentType.NEFT: "NEFT",
            PaymentType.RTGS: "RTGS",
            PaymentType.IMPS: "IMPS",
            PaymentType.INTERNAL_TRANSFER: "INT",
            PaymentType.BILL_PAYMENT: "BILL",
            PaymentType.MERCHANT_PAYMENT: "MERCH"
        }
        
        prefix = prefix_map.get(self.payment_type, "PAY")
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = self.payment_id[:8].upper()
        
        return f"{prefix}{timestamp}{unique_id}"
    
    def can_process(self) -> bool:
        """Check if payment can be processed"""
        return (
            self.status == PaymentStatus.INITIATED and
            self.amount.amount > 0 and
            (not self.fraud_check or not self.fraud_check.is_high_risk())
        )
    
    def can_cancel(self) -> bool:
        """Check if payment can be cancelled"""
        return self.status in [PaymentStatus.INITIATED, PaymentStatus.PENDING]
    
    def can_refund(self) -> bool:
        """Check if payment can be refunded"""
        return self.status == PaymentStatus.COMPLETED
    
    def mark_pending(self, processed_by: str = ""):
        """Mark payment as pending"""
        if self.status != PaymentStatus.INITIATED:
            raise ValueError("Can only mark initiated payments as pending")
        
        self.status = PaymentStatus.PENDING
        self.processed_by = processed_by
        self.processed_at = datetime.utcnow()
        self.version += 1
    
    def mark_processing(self):
        """Mark payment as processing"""
        if self.status != PaymentStatus.PENDING:
            raise ValueError("Can only mark pending payments as processing")
        
        self.status = PaymentStatus.PROCESSING
        self.version += 1
    
    def mark_completed(self, transaction_id: str = ""):
        """Mark payment as completed"""
        if self.status != PaymentStatus.PROCESSING:
            raise ValueError("Can only mark processing payments as completed")
        
        self.status = PaymentStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if transaction_id:
            self.metadata["transaction_id"] = transaction_id
        self.version += 1
    
    def mark_failed(self, reason: str):
        """Mark payment as failed"""
        if self.status in [PaymentStatus.COMPLETED, PaymentStatus.REFUNDED]:
            raise ValueError("Cannot mark completed or refunded payments as failed")
        
        self.status = PaymentStatus.FAILED
        self.failure_reason = reason
        self.completed_at = datetime.utcnow()
        self.version += 1
    
    def cancel(self, reason: str = "", cancelled_by: str = ""):
        """Cancel payment"""
        if not self.can_cancel():
            raise ValueError("Payment cannot be cancelled in current status")
        
        self.status = PaymentStatus.CANCELLED
        self.failure_reason = reason or "Payment cancelled by user"
        self.metadata["cancelled_by"] = cancelled_by
        self.metadata["cancelled_at"] = datetime.utcnow().isoformat()
        self.completed_at = datetime.utcnow()
        self.version += 1
    
    def refund(self, refund_amount: Optional[PaymentAmount] = None, reason: str = "", refunded_by: str = "") -> 'Payment':
        """Create refund payment"""
        if not self.can_refund():
            raise ValueError("Payment cannot be refunded")
        
        refund_amt = refund_amount or self.amount
        if refund_amt.amount > self.amount.amount:
            raise ValueError("Refund amount cannot exceed original payment amount")
        
        # Create refund payment
        refund_payment = Payment(
            payment_type=self.payment_type,
            amount=refund_amt,
            sender=self.receiver,  # Reverse sender and receiver
            receiver=self.sender,
            channel=self.channel,
            description=f"Refund for {self.reference_number}: {reason}",
            initiated_by=refunded_by,
            metadata={
                "original_payment_id": self.payment_id,
                "refund_reason": reason,
                "refund_type": "full" if refund_amt.amount == self.amount.amount else "partial"
            }
        )
        
        # Update original payment status if full refund
        if refund_amt.amount == self.amount.amount:
            self.status = PaymentStatus.REFUNDED
            self.metadata["refunded_at"] = datetime.utcnow().isoformat()
            self.metadata["refund_payment_id"] = refund_payment.payment_id
            self.version += 1
        
        return refund_payment
    
    def set_fraud_check(self, fraud_check: FraudCheck):
        """Set fraud detection result"""
        self.fraud_check = fraud_check
        
        # Auto-fail payments with critical risk
        if fraud_check.risk_level == FraudRiskLevel.CRITICAL:
            self.mark_failed("Payment blocked due to high fraud risk")
        
        self.version += 1
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to payment"""
        self.metadata[key] = value
        self.version += 1
    
    def get_processing_time(self) -> Optional[int]:
        """Get processing time in seconds"""
        if self.completed_at and self.initiated_at:
            return int((self.completed_at - self.initiated_at).total_seconds())
        return None
    
    def is_high_value(self, threshold: Decimal = Decimal('100000')) -> bool:
        """Check if payment is high value"""
        return self.amount.amount >= threshold
    
    def requires_approval(self) -> bool:
        """Check if payment requires manual approval"""
        return (
            self.is_high_value() or
            (self.fraud_check and self.fraud_check.requires_approval())
        )
