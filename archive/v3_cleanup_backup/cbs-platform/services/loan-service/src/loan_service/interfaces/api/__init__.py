"""
Loan Service V2.0 API Interface Layer

This module exposes the API controllers for the loan service.
"""

from .controllers import router

__all__ = ["router"]
from enum import Enum
import logging

from ...domain.entities import (
    Loan, LoanAmount, LoanTerm, LoanType, LoanStatus, RiskCategory
)
from ...infrastructure.repositories import LoanRepositoryInterface
from ...application.services import LoanService

# Setup logging
logger = logging.getLogger(__name__)

# Create router
loan_router = APIRouter(prefix="/api/v1/loans", tags=["loans"])


# Request/Response Models
class LoanTypeEnum(str, Enum):
    PERSONAL = "personal"
    HOME = "home"
    AUTO = "auto"
    BUSINESS = "business"
    EDUCATION = "education"
    GOLD = "gold"
    AGRICULTURE = "agriculture"
    MORTGAGE = "mortgage"


class LoanStatusEnum(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSED = "disbursed"
    ACTIVE = "active"
    COMPLETED = "completed"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class RiskCategoryEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class LoanAmountRequest(BaseModel):
    principal: Decimal = Field(..., gt=0, description="Loan principal amount")
    currency: str = Field("USD", description="Currency code")
    
    @validator('principal')
    def validate_principal(cls, v):
        if v <= 0:
            raise ValueError('Principal amount must be positive')
        return v.quantize(Decimal('0.01'))


class LoanTermRequest(BaseModel):
    interest_rate: Decimal = Field(..., gt=0, description="Interest rate percentage")
    tenure_months: int = Field(..., gt=0, le=360, description="Loan tenure in months")
    emi_amount: Optional[Decimal] = Field(None, description="EMI amount (calculated if not provided)")
    
    @validator('interest_rate')
    def validate_interest_rate(cls, v):
        if not 0 < v <= 50:
            raise ValueError('Interest rate must be between 0 and 50 percent')
        return v.quantize(Decimal('0.0001'))
    
    @validator('tenure_months')
    def validate_tenure(cls, v):
        if not 1 <= v <= 360:
            raise ValueError('Tenure must be between 1 and 360 months')
        return v


class CreateLoanRequest(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    primary_account_id: str = Field(..., description="Primary account for disbursement")
    loan_type: LoanTypeEnum
    loan_purpose: str = Field(..., min_length=10, max_length=500, description="Purpose of loan")
    amount: LoanAmountRequest
    terms: LoanTermRequest
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LoanResponse(BaseModel):
    loan_id: str
    loan_number: str
    customer_id: str
    primary_account_id: str
    loan_type: LoanTypeEnum
    loan_purpose: str
    amount: LoanAmountRequest
    terms: LoanTermRequest
    status: LoanStatusEnum
    risk_category: Optional[RiskCategoryEnum] = None
    approved_amount: Optional[Decimal] = None
    disbursed_amount: Decimal = Decimal('0')
    outstanding_amount: Decimal = Decimal('0')
    credit_score: Optional[int] = None
    debt_to_income_ratio: Optional[Decimal] = None
    application_date: datetime
    approval_date: Optional[datetime] = None
    disbursement_date: Optional[datetime] = None
    maturity_date: Optional[datetime] = None
    next_due_date: Optional[date] = None
    last_payment_date: Optional[datetime] = None
    total_payments_made: int = 0
    total_amount_paid: Decimal = Decimal('0')
    overdue_amount: Decimal = Decimal('0')
    days_past_due: int = 0
    created_by: str
    approved_by: Optional[str] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = {}
    version: int = 1


class EMIScheduleResponse(BaseModel):
    installment_number: int
    emi_amount: Decimal
    principal_amount: Decimal
    interest_amount: Decimal
    due_date: datetime
    outstanding_principal: Decimal
    outstanding_interest: Decimal
    status: str = "pending"
    paid_amount: Decimal = Decimal('0')
    payment_date: Optional[datetime] = None


class LoanSummaryResponse(BaseModel):
    customer_id: str
    total_loans: int
    total_loan_amount: Decimal
    total_outstanding: Decimal
    by_status: Dict[str, Dict[str, Any]]
    by_type: Dict[str, Dict[str, Any]]


class LoanListResponse(BaseModel):
    loans: List[LoanResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool


class ApprovalRequest(BaseModel):
    approved_amount: Decimal = Field(..., gt=0)
    approved_by: str = Field(..., min_length=1)
    conditions: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class RejectionRequest(BaseModel):
    rejected_by: str = Field(..., min_length=1)
    rejection_reason: str = Field(..., min_length=10, max_length=1000)


class DisbursementRequest(BaseModel):
    disbursement_amount: Decimal = Field(..., gt=0)
    disbursement_account: str = Field(..., min_length=1)
    disbursed_by: str = Field(..., min_length=1)
    notes: Optional[str] = None


# Loan Controllers
@loan_router.post("/", response_model=LoanResponse, status_code=201)
async def create_loan_application(
    loan_request: CreateLoanRequest,
    loan_service: LoanService = Depends()
):
    """
    Create a new loan application
    
    Creates a loan application in draft status. The application will need
    to go through review, approval, and disbursement processes.
    """
    try:
        logger.info(f"Creating loan application: {loan_request.loan_type} for {loan_request.amount.principal}")
        
        # Convert request to domain entities
        amount = LoanAmount(
            principal=loan_request.amount.principal,
            currency=loan_request.amount.currency
        )
        
        terms = LoanTerm(
            interest_rate=loan_request.terms.interest_rate,
            tenure_months=loan_request.terms.tenure_months,
            emi_amount=loan_request.terms.emi_amount or Decimal('0')
        )
        
        # Create domain loan
        loan = Loan(
            customer_id=loan_request.customer_id,
            primary_account_id=loan_request.primary_account_id,
            loan_type=LoanType(loan_request.loan_type.value),
            loan_purpose=loan_request.loan_purpose,
            amount=amount,
            terms=terms,
            metadata=loan_request.metadata,
            created_by="api_user"  # TODO: Get from authentication context
        )
        
        # Create loan through service
        created_loan = await loan_service.create_loan_application(loan)
        
        # Convert to response
        response = _loan_to_response(created_loan)
        
        logger.info(f"Loan application created successfully: {created_loan.loan_id}")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error creating loan: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating loan: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@loan_router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(
    loan_id: str = Path(..., description="Loan ID"),
    loan_service: LoanService = Depends()
):
    """
    Get loan details by ID
    
    Retrieves complete loan information including current status,
    amounts, payment history, and terms.
    """
    try:
        loan = await loan_service.get_loan(loan_id)
        
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        return _loan_to_response(loan)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting loan {loan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@loan_router.get("/number/{loan_number}", response_model=LoanResponse)
async def get_loan_by_number(
    loan_number: str = Path(..., description="Loan number"),
    loan_service: LoanService = Depends()
):
    """
    Get loan details by loan number
    
    Retrieves loan information using the human-readable loan number.
    """
    try:
        loan = await loan_service.get_loan_by_number(loan_number)
        
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        return _loan_to_response(loan)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting loan by number {loan_number}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@loan_router.get("/", response_model=LoanListResponse)
async def list_loans(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    status: Optional[LoanStatusEnum] = Query(None, description="Filter by status"),
    loan_type: Optional[LoanTypeEnum] = Query(None, description="Filter by loan type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    loan_service: LoanService = Depends()
):
    """
    List loans with filters and pagination
    
    Retrieves a list of loans based on various filter criteria.
    Supports pagination for large result sets.
    """
    try:
        filters = {}
        if customer_id:
            filters['customer_id'] = customer_id
        if status:
            filters['status'] = LoanStatus(status.value)
        if loan_type:
            filters['loan_type'] = LoanType(loan_type.value)
        
        loans, total_count = await loan_service.list_loans(
            filters=filters,
            page=page,
            page_size=page_size
        )
        
        loan_responses = [_loan_to_response(loan) for loan in loans]
        
        return LoanListResponse(
            loans=loan_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total_count
        )
        
    except Exception as e:
        logger.error(f"Error listing loans: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@loan_router.post("/{loan_id}/approve", response_model=LoanResponse)
async def approve_loan(
    loan_id: str = Path(..., description="Loan ID"),
    approval_request: ApprovalRequest = Body(...),
    loan_service: LoanService = Depends()
):
    """
    Approve a loan application
    
    Approves a loan application that is under review. Sets the approved
    amount and moves the loan to approved status.
    """
    try:
        loan = await loan_service.approve_loan(
            loan_id=loan_id,
            approved_amount=approval_request.approved_amount,
            approved_by=approval_request.approved_by,
            conditions=approval_request.conditions,
            notes=approval_request.notes
        )
        
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        return _loan_to_response(loan)
        
    except ValueError as e:
        logger.error(f"Validation error approving loan {loan_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving loan {loan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@loan_router.post("/{loan_id}/reject", response_model=LoanResponse)
async def reject_loan(
    loan_id: str = Path(..., description="Loan ID"),
    rejection_request: RejectionRequest = Body(...),
    loan_service: LoanService = Depends()
):
    """
    Reject a loan application
    
    Rejects a loan application that is under review. Sets the rejection
    reason and moves the loan to rejected status.
    """
    try:
        loan = await loan_service.reject_loan(
            loan_id=loan_id,
            rejected_by=rejection_request.rejected_by,
            rejection_reason=rejection_request.rejection_reason
        )
        
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        return _loan_to_response(loan)
        
    except ValueError as e:
        logger.error(f"Validation error rejecting loan {loan_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting loan {loan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@loan_router.post("/{loan_id}/disburse", response_model=LoanResponse)
async def disburse_loan(
    loan_id: str = Path(..., description="Loan ID"),
    disbursement_request: DisbursementRequest = Body(...),
    loan_service: LoanService = Depends()
):
    """
    Disburse an approved loan
    
    Disburses funds for an approved loan to the specified account.
    This creates the EMI schedule and activates the loan.
    """
    try:
        loan = await loan_service.disburse_loan(
            loan_id=loan_id,
            disbursement_amount=disbursement_request.disbursement_amount,
            disbursement_account=disbursement_request.disbursement_account,
            disbursed_by=disbursement_request.disbursed_by,
            notes=disbursement_request.notes
        )
        
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        return _loan_to_response(loan)
        
    except ValueError as e:
        logger.error(f"Validation error disbursing loan {loan_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error disbursing loan {loan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@loan_router.get("/{loan_id}/schedule", response_model=List[EMIScheduleResponse])
async def get_emi_schedule(
    loan_id: str = Path(..., description="Loan ID"),
    loan_service: LoanService = Depends()
):
    """
    Get EMI schedule for a loan
    
    Retrieves the complete EMI payment schedule including
    due dates, amounts, and payment status.
    """
    try:
        schedule = await loan_service.get_emi_schedule(loan_id)
        
        if not schedule:
            raise HTTPException(status_code=404, detail="EMI schedule not found")
        
        response = []
        for emi in schedule:
            response.append(EMIScheduleResponse(
                installment_number=emi.installment_number,
                emi_amount=emi.emi_amount,
                principal_amount=emi.principal_amount,
                interest_amount=emi.interest_amount,
                due_date=emi.due_date,
                outstanding_principal=emi.outstanding_principal,
                outstanding_interest=emi.outstanding_interest,
                status=emi.status,
                paid_amount=emi.paid_amount,
                payment_date=emi.payment_date
            ))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting EMI schedule for loan {loan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@loan_router.get("/customers/{customer_id}/summary", response_model=LoanSummaryResponse)
async def get_customer_loan_summary(
    customer_id: str = Path(..., description="Customer ID"),
    loan_service: LoanService = Depends()
):
    """
    Get loan summary for a customer
    
    Provides aggregated loan statistics for the specified customer,
    including totals by status and loan type.
    """
    try:
        summary = await loan_service.get_customer_loan_summary(customer_id)
        
        return LoanSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Error getting loan summary for customer {customer_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@loan_router.get("/overdue", response_model=LoanListResponse)
async def get_overdue_loans(
    days_overdue: int = Query(1, ge=1, description="Minimum days overdue"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    loan_service: LoanService = Depends()
):
    """
    Get overdue loans
    
    Retrieves loans that are overdue by the specified number of days.
    Used for collection management and monitoring.
    """
    try:
        loans = await loan_service.get_overdue_loans(days_overdue)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_loans = loans[start_idx:end_idx]
        
        loan_responses = [_loan_to_response(loan) for loan in paginated_loans]
        
        return LoanListResponse(
            loans=loan_responses,
            total_count=len(loans),
            page=page,
            page_size=page_size,
            has_next=end_idx < len(loans)
        )
        
    except Exception as e:
        logger.error(f"Error getting overdue loans: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@loan_router.get("/portfolio/statistics")
async def get_portfolio_statistics(
    loan_service: LoanService = Depends()
):
    """
    Get loan portfolio statistics
    
    Provides overall portfolio health metrics including
    active loans, overdue amounts, and NPA statistics.
    """
    try:
        stats = await loan_service.get_portfolio_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting portfolio statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@loan_router.post("/{loan_id}/calculate-emi")
async def calculate_emi(
    loan_id: str = Path(..., description="Loan ID"),
    principal: Decimal = Body(..., gt=0),
    interest_rate: Decimal = Body(..., gt=0),
    tenure_months: int = Body(..., gt=0),
    loan_service: LoanService = Depends()
):
    """
    Calculate EMI for given loan parameters
    
    Calculates the EMI amount and provides a preview of the
    payment schedule without creating the actual loan.
    """
    try:
        emi_details = await loan_service.calculate_emi(
            principal=principal,
            interest_rate=interest_rate,
            tenure_months=tenure_months
        )
        
        return emi_details
        
    except Exception as e:
        logger.error(f"Error calculating EMI: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint
@loan_router.get("/health", status_code=200)
async def health_check():
    """
    Health check endpoint for loan service
    """
    return {
        "status": "healthy",
        "service": "loan-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }


# Utility functions
def _loan_to_response(loan: Loan) -> LoanResponse:
    """Convert loan domain entity to response model"""
    return LoanResponse(
        loan_id=loan.loan_id,
        loan_number=loan.loan_number,
        customer_id=loan.customer_id,
        primary_account_id=loan.primary_account_id,
        loan_type=LoanTypeEnum(loan.loan_type.value),
        loan_purpose=loan.loan_purpose,
        amount=LoanAmountRequest(
            principal=loan.amount.principal,
            currency=loan.amount.currency
        ),
        terms=LoanTermRequest(
            interest_rate=loan.terms.interest_rate,
            tenure_months=loan.terms.tenure_months,
            emi_amount=loan.terms.emi_amount
        ),
        status=LoanStatusEnum(loan.status.value),
        risk_category=RiskCategoryEnum(loan.risk_category.value) if loan.risk_category else None,
        approved_amount=loan.approved_amount,
        disbursed_amount=loan.disbursed_amount,
        outstanding_amount=loan.outstanding_amount,
        credit_score=loan.credit_score,
        debt_to_income_ratio=loan.debt_to_income_ratio,
        application_date=loan.application_date,
        approval_date=loan.approval_date,
        disbursement_date=loan.disbursement_date,
        maturity_date=loan.maturity_date,
        next_due_date=loan.next_due_date,
        last_payment_date=loan.last_payment_date,
        total_payments_made=loan.total_payments_made,
        total_amount_paid=loan.total_amount_paid,
        overdue_amount=loan.overdue_amount,
        days_past_due=loan.days_past_due,
        created_by=loan.created_by,
        approved_by=loan.approved_by,
        rejected_by=loan.rejected_by,
        rejection_reason=loan.rejection_reason,
        notes=loan.notes,
        metadata=loan.metadata,
        version=loan.version
    )


# Error handlers
@loan_router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "validation_error"}
    )


@loan_router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "server_error"}
    )


# Export router
__all__ = ['loan_router']
