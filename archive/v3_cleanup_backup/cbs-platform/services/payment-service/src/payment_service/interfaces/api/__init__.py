"""
Payment Service REST API Controllers
Production-ready FastAPI controllers for payment processing
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import logging

from ...domain.entities import (
    Payment, PaymentAmount, PaymentParty, PaymentType, 
    PaymentStatus, PaymentChannel, FraudRiskLevel
)
from ...infrastructure.repositories import PaymentRepositoryInterface
from ...application.services import PaymentService

# Setup logging
logger = logging.getLogger(__name__)

# Create router
payment_router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


# Request/Response Models
class PaymentTypeEnum(str, Enum):
    UPI = "upi"
    NEFT = "neft"
    RTGS = "rtgs"
    IMPS = "imps"
    INTERNAL_TRANSFER = "internal_transfer"
    BILL_PAYMENT = "bill_payment"
    MERCHANT_PAYMENT = "merchant_payment"


class PaymentStatusEnum(str, Enum):
    INITIATED = "initiated"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentChannelEnum(str, Enum):
    MOBILE = "mobile"
    INTERNET_BANKING = "internet_banking"
    ATM = "atm"
    BRANCH = "branch"
    API = "api"


class PaymentAmountRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Payment amount (must be positive)")
    currency: str = Field("USD", description="Currency code (ISO 4217)")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v.quantize(Decimal('0.01'))
    
    @validator('currency')
    def validate_currency(cls, v):
        if len(v) != 3:
            raise ValueError('Currency must be 3-character ISO code')
        return v.upper()


class PaymentPartyRequest(BaseModel):
    account_number: str = Field(..., min_length=1, max_length=50)
    account_name: str = Field(..., min_length=1, max_length=200)
    bank_code: str = Field(..., min_length=1, max_length=20)
    bank_name: str = Field(..., min_length=1, max_length=200)
    branch_code: Optional[str] = Field(None, max_length=20)
    ifsc_code: Optional[str] = Field(None, max_length=20)


class UPIDetailsRequest(BaseModel):
    vpa: str = Field(..., description="Virtual Payment Address")
    merchant_id: Optional[str] = Field(None, max_length=50)
    qr_code: Optional[str] = None
    purpose: str = Field("PAYMENT", max_length=100)
    
    @validator('vpa')
    def validate_vpa(cls, v):
        if '@' not in v:
            raise ValueError('Invalid VPA format')
        return v


class BillPaymentDetailsRequest(BaseModel):
    biller_id: str = Field(..., min_length=1, max_length=50)
    biller_name: str = Field(..., min_length=1, max_length=200)
    bill_number: str = Field(..., min_length=1, max_length=100)
    due_date: Optional[datetime] = None
    bill_amount: Optional[PaymentAmountRequest] = None


class CreatePaymentRequest(BaseModel):
    payment_type: PaymentTypeEnum
    amount: PaymentAmountRequest
    sender: PaymentPartyRequest
    receiver: PaymentPartyRequest
    channel: PaymentChannelEnum = PaymentChannelEnum.API
    description: str = Field("", max_length=500)
    upi_details: Optional[UPIDetailsRequest] = None
    bill_details: Optional[BillPaymentDetailsRequest] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('upi_details')
    def validate_upi_details(cls, v, values):
        if values.get('payment_type') == PaymentTypeEnum.UPI and not v:
            raise ValueError('UPI details required for UPI payments')
        return v
    
    @validator('bill_details')
    def validate_bill_details(cls, v, values):
        if values.get('payment_type') == PaymentTypeEnum.BILL_PAYMENT and not v:
            raise ValueError('Bill details required for bill payments')
        return v


class PaymentResponse(BaseModel):
    payment_id: str
    reference_number: str
    payment_type: PaymentTypeEnum
    status: PaymentStatusEnum
    amount: PaymentAmountRequest
    sender: PaymentPartyRequest
    receiver: PaymentPartyRequest
    channel: PaymentChannelEnum
    description: str
    initiated_at: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = {}
    version: int = 1


class PaymentSummaryResponse(BaseModel):
    account_number: str
    period: Dict[str, str]
    total_transactions: int
    total_amount: Decimal
    by_status: Dict[str, Dict[str, Any]]
    by_type: Dict[str, Dict[str, Any]]


class PaymentListResponse(BaseModel):
    payments: List[PaymentResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool


# Payment Controllers
@payment_router.post("/", response_model=PaymentResponse, status_code=201)
async def create_payment(
    payment_request: CreatePaymentRequest,
    payment_service: PaymentService = Depends()
):
    """
    Create a new payment
    
    This endpoint creates a new payment transaction with fraud detection
    and validation. The payment will be in 'initiated' status initially.
    """
    try:
        logger.info(f"Creating payment: {payment_request.payment_type} for {payment_request.amount.amount}")
        
        # Convert request to domain entities
        amount = PaymentAmount(
            amount=payment_request.amount.amount,
            currency=payment_request.amount.currency
        )
        
        sender = PaymentParty(
            account_number=payment_request.sender.account_number,
            account_name=payment_request.sender.account_name,
            bank_code=payment_request.sender.bank_code,
            bank_name=payment_request.sender.bank_name,
            branch_code=payment_request.sender.branch_code,
            ifsc_code=payment_request.sender.ifsc_code
        )
        
        receiver = PaymentParty(
            account_number=payment_request.receiver.account_number,
            account_name=payment_request.receiver.account_name,
            bank_code=payment_request.receiver.bank_code,
            bank_name=payment_request.receiver.bank_name,
            branch_code=payment_request.receiver.branch_code,
            ifsc_code=payment_request.receiver.ifsc_code
        )
        
        # Create domain payment
        payment = Payment(
            payment_type=PaymentType(payment_request.payment_type.value),
            amount=amount,
            sender=sender,
            receiver=receiver,
            channel=payment_request.channel.value,
            description=payment_request.description,
            metadata=payment_request.metadata
        )
        
        # Add UPI details if provided
        if payment_request.upi_details:
            from ...domain.entities import UPIDetails
            payment.upi_details = UPIDetails(
                vpa=payment_request.upi_details.vpa,
                merchant_id=payment_request.upi_details.merchant_id,
                qr_code=payment_request.upi_details.qr_code,
                purpose=payment_request.upi_details.purpose
            )
        
        # Add bill details if provided
        if payment_request.bill_details:
            from ...domain.entities import BillPaymentDetails
            bill_amount = None
            if payment_request.bill_details.bill_amount:
                bill_amount = PaymentAmount(
                    amount=payment_request.bill_details.bill_amount.amount,
                    currency=payment_request.bill_details.bill_amount.currency
                )
            
            payment.bill_details = BillPaymentDetails(
                biller_id=payment_request.bill_details.biller_id,
                biller_name=payment_request.bill_details.biller_name,
                bill_number=payment_request.bill_details.bill_number,
                due_date=payment_request.bill_details.due_date,
                bill_amount=bill_amount
            )
        
        # Process payment through service
        created_payment = await payment_service.create_payment(payment)
        
        # Convert to response
        response = _payment_to_response(created_payment)
        
        logger.info(f"Payment created successfully: {created_payment.payment_id}")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error creating payment: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@payment_router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str = Path(..., description="Payment ID"),
    payment_service: PaymentService = Depends()
):
    """
    Get payment details by ID
    
    Retrieves complete payment information including status, amounts,
    parties involved, and processing history.
    """
    try:
        payment = await payment_service.get_payment(payment_id)
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return _payment_to_response(payment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment {payment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@payment_router.get("/reference/{reference_number}", response_model=PaymentResponse)
async def get_payment_by_reference(
    reference_number: str = Path(..., description="Payment reference number"),
    payment_service: PaymentService = Depends()
):
    """
    Get payment details by reference number
    
    Retrieves payment information using the human-readable reference number.
    """
    try:
        payment = await payment_service.get_payment_by_reference(reference_number)
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return _payment_to_response(payment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment by reference {reference_number}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@payment_router.get("/", response_model=PaymentListResponse)
async def list_payments(
    account_number: Optional[str] = Query(None, description="Filter by account number"),
    status: Optional[PaymentStatusEnum] = Query(None, description="Filter by status"),
    payment_type: Optional[PaymentTypeEnum] = Query(None, description="Filter by payment type"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    payment_service: PaymentService = Depends()
):
    """
    List payments with filters and pagination
    
    Retrieves a list of payments based on various filter criteria.
    Supports pagination for large result sets.
    """
    try:
        filters = {}
        if account_number:
            filters['account_number'] = account_number
        if status:
            filters['status'] = PaymentStatus(status.value)
        if payment_type:
            filters['payment_type'] = PaymentType(payment_type.value)
        if start_date:
            filters['start_date'] = datetime.combine(start_date, datetime.min.time())
        if end_date:
            filters['end_date'] = datetime.combine(end_date, datetime.max.time())
        
        payments, total_count = await payment_service.list_payments(
            filters=filters,
            page=page,
            page_size=page_size
        )
        
        payment_responses = [_payment_to_response(payment) for payment in payments]
        
        return PaymentListResponse(
            payments=payment_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total_count
        )
        
    except Exception as e:
        logger.error(f"Error listing payments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@payment_router.post("/{payment_id}/process", response_model=PaymentResponse)
async def process_payment(
    payment_id: str = Path(..., description="Payment ID"),
    payment_service: PaymentService = Depends()
):
    """
    Process a payment
    
    Initiates processing of a payment that is in 'initiated' or 'pending' status.
    This will run fraud detection, validate limits, and submit to payment gateway.
    """
    try:
        payment = await payment_service.process_payment(payment_id)
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return _payment_to_response(payment)
        
    except ValueError as e:
        logger.error(f"Validation error processing payment {payment_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing payment {payment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@payment_router.post("/{payment_id}/cancel", response_model=PaymentResponse)
async def cancel_payment(
    payment_id: str = Path(..., description="Payment ID"),
    reason: str = Body(..., description="Cancellation reason"),
    payment_service: PaymentService = Depends()
):
    """
    Cancel a payment
    
    Cancels a payment that is in 'initiated' or 'pending' status.
    Payments that are already processing or completed cannot be cancelled.
    """
    try:
        payment = await payment_service.cancel_payment(payment_id, reason)
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return _payment_to_response(payment)
        
    except ValueError as e:
        logger.error(f"Validation error cancelling payment {payment_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling payment {payment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@payment_router.get("/accounts/{account_number}/summary", response_model=PaymentSummaryResponse)
async def get_payment_summary(
    account_number: str = Path(..., description="Account number"),
    start_date: date = Query(..., description="Summary start date"),
    end_date: date = Query(..., description="Summary end date"),
    payment_service: PaymentService = Depends()
):
    """
    Get payment summary for an account
    
    Provides aggregated payment statistics for the specified account
    and date range, including totals by status and payment type.
    """
    try:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        summary = await payment_service.get_payment_summary(
            account_number, start_datetime, end_datetime
        )
        
        return PaymentSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Error getting payment summary for {account_number}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@payment_router.get("/high-value", response_model=PaymentListResponse)
async def get_high_value_payments(
    amount_threshold: Decimal = Query(Decimal('100000'), description="Amount threshold"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    payment_service: PaymentService = Depends()
):
    """
    Get high value payments requiring approval
    
    Retrieves payments that exceed the specified amount threshold
    and may require manual approval or additional verification.
    """
    try:
        payments = await payment_service.get_high_value_payments(
            amount_threshold, page, page_size
        )
        
        payment_responses = [_payment_to_response(payment) for payment in payments]
        
        return PaymentListResponse(
            payments=payment_responses,
            total_count=len(payment_responses),
            page=page,
            page_size=page_size,
            has_next=len(payment_responses) == page_size
        )
        
    except Exception as e:
        logger.error(f"Error getting high value payments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@payment_router.get("/suspicious", response_model=PaymentListResponse)
async def get_suspicious_payments(
    risk_threshold: int = Query(70, ge=0, le=100, description="Risk score threshold"),
    payment_service: PaymentService = Depends()
):
    """
    Get payments flagged as suspicious
    
    Retrieves payments with high fraud risk scores that may require
    manual review or additional verification.
    """
    try:
        payments = await payment_service.get_suspicious_payments(risk_threshold)
        
        payment_responses = [_payment_to_response(payment) for payment in payments]
        
        return PaymentListResponse(
            payments=payment_responses,
            total_count=len(payment_responses),
            page=1,
            page_size=len(payment_responses),
            has_next=False
        )
        
    except Exception as e:
        logger.error(f"Error getting suspicious payments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint
@payment_router.get("/health", status_code=200)
async def health_check():
    """
    Health check endpoint for payment service
    """
    return {
        "status": "healthy",
        "service": "payment-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }


# Utility functions
def _payment_to_response(payment: Payment) -> PaymentResponse:
    """Convert payment domain entity to response model"""
    return PaymentResponse(
        payment_id=payment.payment_id,
        reference_number=payment.reference_number,
        payment_type=PaymentTypeEnum(payment.payment_type.value),
        status=PaymentStatusEnum(payment.status.value),
        amount=PaymentAmountRequest(
            amount=payment.amount.amount,
            currency=payment.amount.currency
        ),
        sender=PaymentPartyRequest(
            account_number=payment.sender.account_number,
            account_name=payment.sender.account_name,
            bank_code=payment.sender.bank_code,
            bank_name=payment.sender.bank_name,
            branch_code=payment.sender.branch_code,
            ifsc_code=payment.sender.ifsc_code
        ),
        receiver=PaymentPartyRequest(
            account_number=payment.receiver.account_number,
            account_name=payment.receiver.account_name,
            bank_code=payment.receiver.bank_code,
            bank_name=payment.receiver.bank_name,
            branch_code=payment.receiver.branch_code,
            ifsc_code=payment.receiver.ifsc_code
        ),
        channel=PaymentChannelEnum(payment.channel.value),
        description=payment.description,
        initiated_at=payment.initiated_at,
        processed_at=payment.processed_at,
        completed_at=payment.completed_at,
        failure_reason=payment.failure_reason,
        metadata=payment.metadata,
        version=payment.version
    )


# Error handlers
@payment_router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "validation_error"}
    )


@payment_router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "server_error"}
    )


# Export router
__all__ = ['payment_router']
