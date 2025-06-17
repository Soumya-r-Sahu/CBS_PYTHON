"""
Loan Service DTOs
Data Transfer Objects for loan operations
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ...domain.entities import LoanType, LoanStatus, RepaymentFrequency


@dataclass
class LoanAmountDTO:
    """Loan amount data transfer object"""
    amount: Decimal
    currency: str = "USD"


@dataclass
class BorrowerDTO:
    """Borrower data transfer object"""
    customer_id: str
    name: str
    email: str
    phone: str
    address: str
    employment_type: str
    monthly_income: LoanAmountDTO
    existing_obligations: LoanAmountDTO
    credit_score: Optional[int] = None


@dataclass
class CollateralDTO:
    """Collateral data transfer object"""
    collateral_id: str
    type: str
    description: str
    value: LoanAmountDTO
    ownership_documents: List[str]
    valuation_date: Optional[date] = None
    valuator_name: Optional[str] = None


@dataclass
class CreateLoanApplicationRequest:
    """Request to create a new loan application"""
    loan_type: LoanType
    purpose: str
    requested_amount: LoanAmountDTO
    requested_term_months: int
    borrower: BorrowerDTO
    co_borrowers: List[BorrowerDTO] = None
    collaterals: List[CollateralDTO] = None
    repayment_frequency: RepaymentFrequency = RepaymentFrequency.MONTHLY

    def __post_init__(self):
        if self.co_borrowers is None:
            self.co_borrowers = []
        if self.collaterals is None:
            self.collaterals = []


@dataclass
class LoanApplicationResponse:
    """Loan application response data transfer object"""
    application_id: str
    loan_type: LoanType
    purpose: str
    requested_amount: LoanAmountDTO
    requested_term_months: int
    borrower: BorrowerDTO
    co_borrowers: List[BorrowerDTO]
    collaterals: List[CollateralDTO]
    status: LoanStatus
    application_date: date
    processed_by: Optional[str] = None
    processed_date: Optional[date] = None
    remarks: str = ""
    required_documents: List[str] = None
    submitted_documents: List[str] = None
    credit_score: Optional[int] = None
    risk_assessment: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.required_documents is None:
            self.required_documents = []
        if self.submitted_documents is None:
            self.submitted_documents = []


@dataclass
class ProcessLoanApplicationRequest:
    """Request to process loan application"""
    application_id: str
    action: str  # APPROVE, REJECT, REQUEST_DOCUMENTS
    processed_by: str
    remarks: str = ""
    approved_amount: Optional[LoanAmountDTO] = None
    approved_term_months: Optional[int] = None
    approved_interest_rate: Optional[Decimal] = None
    conditions: List[str] = None

    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []


@dataclass
class EMIScheduleDTO:
    """EMI schedule entry data transfer object"""
    installment_number: int
    due_date: date
    principal_amount: LoanAmountDTO
    interest_amount: LoanAmountDTO
    total_amount: LoanAmountDTO
    outstanding_balance: LoanAmountDTO
    payment_status: str
    paid_date: Optional[date] = None
    paid_amount: LoanAmountDTO = None


@dataclass
class LoanResponse:
    """Loan response data transfer object"""
    loan_id: str
    loan_number: str
    application_id: str
    loan_type: LoanType
    purpose: str
    principal_amount: LoanAmountDTO
    outstanding_balance: LoanAmountDTO
    interest_rate: Decimal
    loan_term_months: int
    repayment_frequency: RepaymentFrequency
    borrower: BorrowerDTO
    co_borrowers: List[BorrowerDTO]
    collaterals: List[CollateralDTO]
    disbursement_date: Optional[date] = None
    first_emi_date: Optional[date] = None
    maturity_date: Optional[date] = None
    status: LoanStatus
    emi_amount: LoanAmountDTO
    loan_account_number: str
    disbursement_account: str
    created_at: datetime
    updated_at: datetime

    def __post_init__(self):
        if self.co_borrowers is None:
            self.co_borrowers = []
        if self.collaterals is None:
            self.collaterals = []


@dataclass
class DisburseLoanRequest:
    """Request to disburse loan"""
    loan_id: str
    disbursement_account: str
    disbursement_date: date
    disbursed_by: str
    disbursement_reference: str = ""


@dataclass
class LoanPaymentRequest:
    """Request to make loan payment"""
    loan_id: str
    payment_amount: LoanAmountDTO
    payment_date: date
    payment_reference: str
    payment_mode: str  # CASH, CHEQUE, ONLINE, AUTO_DEBIT
    paid_by: str


@dataclass
class LoanPaymentResponse:
    """Loan payment response"""
    payment_id: str
    loan_id: str
    payment_amount: LoanAmountDTO
    payment_date: date
    payment_reference: str
    payment_mode: str
    updated_outstanding_balance: LoanAmountDTO
    emis_affected: List[EMIScheduleDTO]
    payment_status: str


@dataclass
class LoanListRequest:
    """Request to list loans with filters"""
    customer_id: Optional[str] = None
    loan_type: Optional[LoanType] = None
    status: Optional[LoanStatus] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    overdue_only: bool = False
    page: int = 1
    size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"


@dataclass
class LoanListResponse:
    """Response for loan list"""
    loans: List[LoanResponse]
    total_count: int
    page: int
    size: int
    total_pages: int


@dataclass
class LoanStatsRequest:
    """Request for loan statistics"""
    from_date: date
    to_date: date
    loan_type: Optional[LoanType] = None
    status: Optional[LoanStatus] = None
    group_by: str = "month"  # day, week, month, year


@dataclass
class LoanStatsResponse:
    """Loan statistics response"""
    total_loans: int
    total_disbursed_amount: LoanAmountDTO
    total_outstanding_amount: LoanAmountDTO
    average_loan_amount: LoanAmountDTO
    loans_by_type: Dict[str, int]
    loans_by_status: Dict[str, int]
    overdue_loans: int
    overdue_amount: LoanAmountDTO
    collection_efficiency: float
    npa_percentage: float
    period_stats: List[Dict[str, Any]]


@dataclass
class LoanEligibilityRequest:
    """Request to check loan eligibility"""
    customer_id: str
    loan_type: LoanType
    requested_amount: LoanAmountDTO
    requested_term_months: int
    monthly_income: LoanAmountDTO
    existing_obligations: LoanAmountDTO
    credit_score: Optional[int] = None
    collateral_value: Optional[LoanAmountDTO] = None


@dataclass
class LoanEligibilityResponse:
    """Loan eligibility response"""
    is_eligible: bool
    eligible_amount: LoanAmountDTO
    max_term_months: int
    suggested_interest_rate: Decimal
    eligibility_factors: Dict[str, Any]
    required_documents: List[str]
    conditions: List[str]
    reasons: List[str]  # If not eligible


@dataclass
class PrepaymentRequest:
    """Request for loan prepayment"""
    loan_id: str
    prepayment_amount: LoanAmountDTO
    prepayment_date: date
    prepayment_charges: LoanAmountDTO = None
    prepaid_by: str
    reason: str = ""


@dataclass
class PrepaymentResponse:
    """Prepayment response"""
    prepayment_id: str
    loan_id: str
    prepayment_amount: LoanAmountDTO
    prepayment_charges: LoanAmountDTO
    total_deduction: LoanAmountDTO
    new_outstanding_balance: LoanAmountDTO
    savings_in_interest: LoanAmountDTO
    revised_emi_amount: Optional[LoanAmountDTO] = None
    revised_maturity_date: Optional[date] = None
    is_loan_closed: bool = False


@dataclass
class LoanDefaultRequest:
    """Request to mark loan as default"""
    loan_id: str
    default_reason: str
    marked_by: str
    recovery_action: str = ""


@dataclass
class LoanWriteOffRequest:
    """Request to write off loan"""
    loan_id: str
    write_off_amount: LoanAmountDTO
    write_off_reason: str
    approved_by: str
    recovery_potential: str = ""


@dataclass
class CollectionSummaryRequest:
    """Request for collection summary"""
    from_date: date
    to_date: date
    loan_type: Optional[LoanType] = None
    overdue_bucket: Optional[str] = None  # 0-30, 31-60, 61-90, 90+


@dataclass
class CollectionSummaryResponse:
    """Collection summary response"""
    total_due_amount: LoanAmountDTO
    total_collected_amount: LoanAmountDTO
    collection_efficiency: float
    overdue_buckets: Dict[str, Dict[str, Any]]
    follow_up_required: List[str]  # Loan IDs requiring follow-up


@dataclass
class LoanValidationError:
    """Loan validation error"""
    field: str
    message: str
    code: str


@dataclass
class LoanValidationResult:
    """Loan validation result"""
    is_valid: bool
    errors: List[LoanValidationError]


# Mapper functions to convert between domain entities and DTOs

def loan_amount_to_dto(amount) -> LoanAmountDTO:
    """Convert LoanAmount entity to DTO"""
    return LoanAmountDTO(
        amount=amount.amount,
        currency=amount.currency
    )


def borrower_to_dto(borrower) -> BorrowerDTO:
    """Convert Borrower entity to DTO"""
    return BorrowerDTO(
        customer_id=borrower.customer_id,
        name=borrower.name,
        email=borrower.email,
        phone=borrower.phone,
        address=borrower.address,
        employment_type=borrower.employment_type,
        monthly_income=loan_amount_to_dto(borrower.monthly_income),
        existing_obligations=loan_amount_to_dto(borrower.existing_obligations),
        credit_score=borrower.credit_score
    )


def collateral_to_dto(collateral) -> CollateralDTO:
    """Convert Collateral entity to DTO"""
    return CollateralDTO(
        collateral_id=collateral.collateral_id,
        type=collateral.type.value,
        description=collateral.description,
        value=loan_amount_to_dto(collateral.value),
        ownership_documents=collateral.ownership_documents.copy(),
        valuation_date=collateral.valuation_date,
        valuator_name=collateral.valuator_name
    )


def emi_schedule_to_dto(emi) -> EMIScheduleDTO:
    """Convert EMISchedule entity to DTO"""
    return EMIScheduleDTO(
        installment_number=emi.installment_number,
        due_date=emi.due_date,
        principal_amount=loan_amount_to_dto(emi.principal_amount),
        interest_amount=loan_amount_to_dto(emi.interest_amount),
        total_amount=loan_amount_to_dto(emi.total_amount),
        outstanding_balance=loan_amount_to_dto(emi.outstanding_balance),
        payment_status=emi.payment_status.value,
        paid_date=emi.paid_date,
        paid_amount=loan_amount_to_dto(emi.paid_amount) if emi.paid_amount else None
    )


def loan_application_to_response(application) -> LoanApplicationResponse:
    """Convert LoanApplication entity to response DTO"""
    return LoanApplicationResponse(
        application_id=application.application_id,
        loan_type=application.loan_type,
        purpose=application.purpose,
        requested_amount=loan_amount_to_dto(application.requested_amount),
        requested_term_months=application.requested_term.to_months(),
        borrower=borrower_to_dto(application.borrower),
        co_borrowers=[borrower_to_dto(cb) for cb in application.co_borrowers],
        collaterals=[collateral_to_dto(c) for c in application.collaterals],
        status=application.status,
        application_date=application.application_date,
        processed_by=application.processed_by,
        processed_date=application.processed_date,
        remarks=application.remarks,
        required_documents=application.required_documents.copy(),
        submitted_documents=application.submitted_documents.copy()
    )


def loan_to_response(loan) -> LoanResponse:
    """Convert Loan entity to response DTO"""
    return LoanResponse(
        loan_id=loan.loan_id,
        loan_number=loan.loan_number,
        application_id=loan.application_id,
        loan_type=loan.loan_type,
        purpose=loan.purpose,
        principal_amount=loan_amount_to_dto(loan.principal_amount),
        outstanding_balance=loan_amount_to_dto(loan.outstanding_balance),
        interest_rate=loan.interest_rate.get_effective_rate(),
        loan_term_months=loan.loan_term.to_months(),
        repayment_frequency=loan.repayment_frequency,
        borrower=borrower_to_dto(loan.borrower),
        co_borrowers=[borrower_to_dto(cb) for cb in loan.co_borrowers],
        collaterals=[collateral_to_dto(c) for c in loan.collaterals],
        disbursement_date=loan.disbursement_date,
        first_emi_date=loan.first_emi_date,
        maturity_date=loan.maturity_date,
        status=loan.status,
        emi_amount=loan_amount_to_dto(loan.emi_amount),
        loan_account_number=loan.loan_account_number,
        disbursement_account=loan.disbursement_account,
        created_at=loan.created_at,
        updated_at=loan.updated_at
    )
