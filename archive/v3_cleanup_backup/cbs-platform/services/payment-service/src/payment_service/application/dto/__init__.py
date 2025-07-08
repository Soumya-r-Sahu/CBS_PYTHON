"""
Payment Service DTOs
Data Transfer Objects for payment operations
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ...domain.entities import PaymentType, PaymentStatus, PaymentChannel, FraudRiskLevel


@dataclass
class PaymentAmountDTO:
    """Payment amount data transfer object"""
    amount: Decimal
    currency: str = "USD"


@dataclass
class PaymentPartyDTO:
    """Payment party data transfer object"""
    account_number: str
    account_name: str
    bank_code: str
    bank_name: str
    branch_code: Optional[str] = None
    ifsc_code: Optional[str] = None


@dataclass
class UPIDetailsDTO:
    """UPI details data transfer object"""
    vpa: str
    merchant_id: Optional[str] = None
    qr_code: Optional[str] = None
    purpose: str = "PAYMENT"


@dataclass
class BillPaymentDetailsDTO:
    """Bill payment details data transfer object"""
    biller_id: str
    biller_name: str
    bill_number: str
    due_date: Optional[datetime] = None
    bill_amount: Optional[PaymentAmountDTO] = None


@dataclass
class CreatePaymentRequest:
    """Request to create a new payment"""
    payment_type: PaymentType
    amount: PaymentAmountDTO
    sender: PaymentPartyDTO
    receiver: PaymentPartyDTO
    channel: PaymentChannel
    description: str = ""
    upi_details: Optional[UPIDetailsDTO] = None
    bill_details: Optional[BillPaymentDetailsDTO] = None
    initiated_by: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UpdatePaymentRequest:
    """Request to update payment"""
    payment_id: str
    status: Optional[PaymentStatus] = None
    failure_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProcessPaymentRequest:
    """Request to process a payment"""
    payment_id: str
    processed_by: str
    fraud_check_required: bool = True


@dataclass
class CancelPaymentRequest:
    """Request to cancel a payment"""
    payment_id: str
    reason: str
    cancelled_by: str


@dataclass
class RefundPaymentRequest:
    """Request to refund a payment"""
    payment_id: str
    refund_amount: Optional[PaymentAmountDTO] = None
    reason: str
    refunded_by: str


@dataclass
class FraudCheckDTO:
    """Fraud check result data transfer object"""
    risk_level: FraudRiskLevel
    risk_score: int
    flags: List[str]
    checked_at: datetime


@dataclass
class PaymentResponse:
    """Payment response data transfer object"""
    payment_id: str
    payment_type: PaymentType
    amount: PaymentAmountDTO
    sender: PaymentPartyDTO
    receiver: PaymentPartyDTO
    status: PaymentStatus
    channel: PaymentChannel
    reference_number: str
    description: str
    upi_details: Optional[UPIDetailsDTO] = None
    bill_details: Optional[BillPaymentDetailsDTO] = None
    fraud_check: Optional[FraudCheckDTO] = None
    initiated_at: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    initiated_by: Optional[str] = None
    processed_by: Optional[str] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = None
    version: int = 1

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PaymentListRequest:
    """Request to list payments with filters"""
    customer_id: Optional[str] = None
    account_number: Optional[str] = None
    payment_type: Optional[PaymentType] = None
    status: Optional[PaymentStatus] = None
    channel: Optional[PaymentChannel] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    page: int = 1
    size: int = 20
    sort_by: str = "initiated_at"
    sort_order: str = "desc"


@dataclass
class PaymentListResponse:
    """Response for payment list"""
    payments: List[PaymentResponse]
    total_count: int
    page: int
    size: int
    total_pages: int


@dataclass
class PaymentStatsRequest:
    """Request for payment statistics"""
    from_date: datetime
    to_date: datetime
    group_by: str = "day"  # day, week, month
    payment_type: Optional[PaymentType] = None
    status: Optional[PaymentStatus] = None


@dataclass
class PaymentStatsResponse:
    """Payment statistics response"""
    total_payments: int
    total_amount: PaymentAmountDTO
    success_rate: float
    average_processing_time: float
    payment_type_breakdown: Dict[str, int]
    status_breakdown: Dict[str, int]
    daily_stats: List[Dict[str, Any]]


@dataclass
class PaymentValidationError:
    """Payment validation error"""
    field: str
    message: str
    code: str


@dataclass
class PaymentValidationResult:
    """Payment validation result"""
    is_valid: bool
    errors: List[PaymentValidationError]


@dataclass
class PaymentLimitCheckRequest:
    """Request to check payment limits"""
    account_number: str
    payment_type: PaymentType
    amount: PaymentAmountDTO
    daily_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None


@dataclass
class PaymentLimitCheckResponse:
    """Payment limit check response"""
    is_within_limits: bool
    daily_usage: PaymentAmountDTO
    monthly_usage: PaymentAmountDTO
    daily_limit: PaymentAmountDTO
    monthly_limit: PaymentAmountDTO
    violations: List[str]


# Mapper functions to convert between domain entities and DTOs

def payment_amount_to_dto(amount) -> PaymentAmountDTO:
    """Convert PaymentAmount entity to DTO"""
    return PaymentAmountDTO(
        amount=amount.amount,
        currency=amount.currency
    )


def payment_party_to_dto(party) -> PaymentPartyDTO:
    """Convert PaymentParty entity to DTO"""
    return PaymentPartyDTO(
        account_number=party.account_number,
        account_name=party.account_name,
        bank_code=party.bank_code,
        bank_name=party.bank_name,
        branch_code=party.branch_code,
        ifsc_code=party.ifsc_code
    )


def upi_details_to_dto(upi_details) -> Optional[UPIDetailsDTO]:
    """Convert UPIDetails entity to DTO"""
    if not upi_details:
        return None
    
    return UPIDetailsDTO(
        vpa=upi_details.vpa,
        merchant_id=upi_details.merchant_id,
        qr_code=upi_details.qr_code,
        purpose=upi_details.purpose
    )


def bill_details_to_dto(bill_details) -> Optional[BillPaymentDetailsDTO]:
    """Convert BillPaymentDetails entity to DTO"""
    if not bill_details:
        return None
    
    return BillPaymentDetailsDTO(
        biller_id=bill_details.biller_id,
        biller_name=bill_details.biller_name,
        bill_number=bill_details.bill_number,
        due_date=bill_details.due_date,
        bill_amount=payment_amount_to_dto(bill_details.bill_amount) if bill_details.bill_amount else None
    )


def fraud_check_to_dto(fraud_check) -> Optional[FraudCheckDTO]:
    """Convert FraudCheck entity to DTO"""
    if not fraud_check:
        return None
    
    return FraudCheckDTO(
        risk_level=fraud_check.risk_level,
        risk_score=fraud_check.risk_score,
        flags=fraud_check.flags.copy(),
        checked_at=fraud_check.checked_at
    )


def payment_to_response(payment) -> PaymentResponse:
    """Convert Payment entity to response DTO"""
    return PaymentResponse(
        payment_id=payment.payment_id,
        payment_type=payment.payment_type,
        amount=payment_amount_to_dto(payment.amount),
        sender=payment_party_to_dto(payment.sender),
        receiver=payment_party_to_dto(payment.receiver),
        status=payment.status,
        channel=payment.channel,
        reference_number=payment.reference_number,
        description=payment.description,
        upi_details=upi_details_to_dto(payment.upi_details),
        bill_details=bill_details_to_dto(payment.bill_details),
        fraud_check=fraud_check_to_dto(payment.fraud_check),
        initiated_at=payment.initiated_at,
        processed_at=payment.processed_at,
        completed_at=payment.completed_at,
        initiated_by=payment.initiated_by,
        processed_by=payment.processed_by,
        failure_reason=payment.failure_reason,
        metadata=payment.metadata.copy(),
        version=payment.version
    )
