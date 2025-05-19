"""
Loan API Endpoints

This module provides REST API endpoints for loan operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import date

from ...domain.entities.loan import LoanType, LoanStatus, RepaymentFrequency
from ...application.use_cases.loan_application_use_case import LoanApplicationUseCase, LoanApplicationError
from ...application.use_cases.loan_approval_use_case import LoanApprovalUseCase, LoanApprovalError
from ...application.use_cases.loan_disbursement_use_case import LoanDisbursementUseCase, LoanDisbursementError
from ...application.services.loan_calculator_service import LoanCalculatorService

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

from ...di_container import (
    get_loan_application_use_case,
    get_loan_approval_use_case,
    get_loan_disbursement_use_case,
    get_loan_calculator_service,
    get_loan_repository
)


# Create router
router = APIRouter(
    prefix="/api/loans",
    tags=["loans"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models for request/response
class LoanApplicationRequest(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    loan_type: str = Field(..., description="Type of loan")
    amount: float = Field(..., description="Loan amount")
    term_months: int = Field(..., description="Loan term in months")
    interest_rate: float = Field(..., description="Annual interest rate")
    repayment_frequency: str = Field(..., description="Repayment frequency")
    purpose: str = Field(..., description="Purpose of the loan")
    collateral_description: Optional[str] = Field(None, description="Description of collateral")
    collateral_value: Optional[float] = Field(None, description="Value of collateral")
    cosigner_id: Optional[str] = Field(None, description="Cosigner ID")
    grace_period_days: int = Field(0, description="Grace period in days")
    
    @validator('loan_type')
    def validate_loan_type(cls, v):
        if v not in [t.value for t in LoanType]:
            raise ValueError(f'Invalid loan type. Must be one of: {", ".join([t.value for t in LoanType])}')
        return v
    
    @validator('repayment_frequency')
    def validate_repayment_frequency(cls, v):
        if v not in [f.value for f in RepaymentFrequency]:
            raise ValueError(f'Invalid repayment frequency. Must be one of: {", ".join([f.value for f in RepaymentFrequency])}')
        return v
    
    @validator('amount', 'interest_rate')
    def validate_positive_number(cls, v, values, **kwargs):
        if v <= 0:
            field = kwargs.get('field', 'value')
            raise ValueError(f'{field.title()} must be positive')
        return v
    
    @validator('term_months')
    def validate_term_months(cls, v):
        if v <= 0:
            raise ValueError('Term months must be positive')
        if v > 360:  # 30 years maximum
            raise ValueError('Term months cannot exceed 360 (30 years)')
        return v


class LoanApprovalRequest(BaseModel):
    approved_by: str = Field(..., description="Staff ID of approver")
    approved_amount: Optional[float] = Field(None, description="Approved loan amount")
    approved_interest_rate: Optional[float] = Field(None, description="Approved interest rate")
    approval_notes: Optional[str] = Field(None, description="Approval notes")


class LoanDenialRequest(BaseModel):
    denied_by: str = Field(..., description="Staff ID of person denying the loan")
    denial_reason: str = Field(..., description="Reason for denial")
    denial_notes: Optional[str] = Field(None, description="Additional notes")


class LoanDisbursementRequest(BaseModel):
    disbursed_by: str = Field(..., description="Staff ID of person disbursing the loan")
    account_number: str = Field(..., description="Account number to receive funds")
    reference_number: Optional[str] = Field(None, description="Reference number for the transaction")
    disbursement_notes: Optional[str] = Field(None, description="Additional notes")


class LoanCalculatorRequest(BaseModel):
    amount: float = Field(..., description="Loan amount")
    interest_rate: float = Field(..., description="Annual interest rate")
    term_months: int = Field(..., description="Loan term in months")


class LoanTermsResponse(BaseModel):
    interest_rate: float
    term_months: int
    repayment_frequency: str
    grace_period_days: int
    early_repayment_penalty: Optional[float] = None
    
    class Config:
        orm_mode = True


class LoanResponse(BaseModel):
    id: str
    customer_id: str
    loan_type: str
    amount: float
    terms: LoanTermsResponse
    status: str
    purpose: str
    application_date: date
    approved_date: Optional[date] = None
    disbursement_date: Optional[date] = None
    maturity_date: Optional[date] = None
    account_number: Optional[str] = None
    collateral_description: Optional[str] = None
    collateral_value: Optional[float] = None
    
    class Config:
        orm_mode = True


class LoanCalculatorResponse(BaseModel):
    amount: float
    interest_rate: float
    term_months: int
    monthly_payment: float
    total_payment: float
    total_interest: float
    interest_to_principal_ratio: float


class LoanListResponse(BaseModel):
    loans: List[LoanResponse]
    total: int


# API Endpoints
@router.post("/apply", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_loan(
    request: LoanApplicationRequest,
    loan_application_use_case: LoanApplicationUseCase = Depends(get_loan_application_use_case)
):
    """Submit a new loan application."""
    try:
        # Convert string values to enum types
        loan_type_enum = LoanType(request.loan_type)
        repayment_frequency_enum = RepaymentFrequency(request.repayment_frequency)
        
        # Convert numeric values to Decimal
        amount_decimal = Decimal(str(request.amount))
        interest_rate_decimal = Decimal(str(request.interest_rate))
        collateral_value_decimal = Decimal(str(request.collateral_value)) if request.collateral_value else None
        
        # Execute the use case
        loan = loan_application_use_case.execute(
            customer_id=request.customer_id,
            loan_type=loan_type_enum,
            amount=amount_decimal,
            term_months=request.term_months,
            interest_rate=interest_rate_decimal,
            repayment_frequency=repayment_frequency_enum,
            purpose=request.purpose,
            collateral_description=request.collateral_description,
            collateral_value=collateral_value_decimal,
            cosigner_id=request.cosigner_id,
            grace_period_days=request.grace_period_days
        )
        
        return loan
        
    except LoanApplicationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{loan_id}/approve", response_model=LoanResponse)
async def approve_loan(
    loan_id: str,
    request: LoanApprovalRequest,
    loan_approval_use_case: LoanApprovalUseCase = Depends(get_loan_approval_use_case)
):
    """Approve a loan application."""
    try:
        # Convert numeric values to Decimal if provided
        approved_amount_decimal = Decimal(str(request.approved_amount)) if request.approved_amount else None
        approved_interest_rate_decimal = Decimal(str(request.approved_interest_rate)) if request.approved_interest_rate else None
        
        # Execute the use case
        loan = loan_approval_use_case.approve(
            loan_id=loan_id,
            approved_by=request.approved_by,
            approved_amount=approved_amount_decimal,
            approved_interest_rate=approved_interest_rate_decimal,
            approval_notes=request.approval_notes
        )
        
        return loan
        
    except LoanApprovalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{loan_id}/deny", response_model=LoanResponse)
async def deny_loan(
    loan_id: str,
    request: LoanDenialRequest,
    loan_approval_use_case: LoanApprovalUseCase = Depends(get_loan_approval_use_case)
):
    """Deny a loan application."""
    try:
        # Execute the use case
        loan = loan_approval_use_case.deny(
            loan_id=loan_id,
            denied_by=request.denied_by,
            denial_reason=request.denial_reason,
            denial_notes=request.denial_notes
        )
        
        return loan
        
    except LoanApprovalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{loan_id}/disburse", response_model=LoanResponse)
async def disburse_loan(
    loan_id: str,
    request: LoanDisbursementRequest,
    loan_disbursement_use_case: LoanDisbursementUseCase = Depends(get_loan_disbursement_use_case)
):
    """Disburse funds for an approved loan."""
    try:
        # Execute the use case
        loan = loan_disbursement_use_case.execute(
            loan_id=loan_id,
            disbursed_by=request.disbursed_by,
            account_number=request.account_number,
            reference_number=request.reference_number,
            disbursement_notes=request.disbursement_notes
        )
        
        return loan
        
    except LoanDisbursementError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(
    loan_id: str,
    loan_repository = Depends(get_loan_repository)
):
    """Get loan details by ID."""
    loan = loan_repository.get_by_id(loan_id)
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    return loan


@router.get("/", response_model=LoanListResponse)
async def list_loans(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    loan_type: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    loan_repository = Depends(get_loan_repository)
):
    """List loans with optional filtering."""
    # Prepare filters
    filters = {}
    if customer_id:
        filters['customer_id'] = customer_id
    if status:
        try:
            filters['status'] = LoanStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Invalid status. Must be one of: {', '.join([s.value for s in LoanStatus])}"
            )
    if loan_type:
        try:
            filters['loan_type'] = LoanType(loan_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Invalid loan type. Must be one of: {', '.join([t.value for t in LoanType])}"
            )
    
    # Get loans
    loans = loan_repository.find_by(filters, limit=limit, offset=offset)
    total = loan_repository.count(filters)
    
    return {"loans": loans, "total": total}


@router.post("/calculator", response_model=LoanCalculatorResponse)
async def calculate_loan(
    request: LoanCalculatorRequest,
    calculator: LoanCalculatorService = Depends(get_loan_calculator_service)
):
    """Calculate loan EMI and payment details."""
    try:
        # Convert numeric values to Decimal
        amount_decimal = Decimal(str(request.amount))
        interest_rate_decimal = Decimal(str(request.interest_rate))
        
        # Calculate loan details
        emi = calculator.calculate_emi(amount_decimal, interest_rate_decimal, request.term_months)
        total_payment = calculator.calculate_total_payment(amount_decimal, interest_rate_decimal, request.term_months)
        total_interest = calculator.calculate_total_interest(amount_decimal, interest_rate_decimal, request.term_months)
        interest_ratio = (total_interest / amount_decimal * 100).quantize(Decimal('0.01'))
        
        return {
            "amount": float(amount_decimal),
            "interest_rate": float(interest_rate_decimal),
            "term_months": request.term_months,
            "monthly_payment": float(emi),
            "total_payment": float(total_payment),
            "total_interest": float(total_interest),
            "interest_to_principal_ratio": float(interest_ratio)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
