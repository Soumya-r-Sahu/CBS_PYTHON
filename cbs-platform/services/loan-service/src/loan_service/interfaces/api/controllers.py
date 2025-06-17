"""
Loan Service V2.0 API Controllers

This module provides comprehensive FastAPI endpoints for loan management,
including loan applications, approvals, disbursements, payments, and queries.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
import uuid

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator


# Pydantic Models for API
class LoanApplicationCreateModel(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    loan_type: str = Field(..., description="Type of loan")
    loan_purpose: str = Field(..., description="Purpose of loan")
    requested_amount: Decimal = Field(..., gt=0, description="Requested loan amount")
    tenure_months: int = Field(..., gt=0, le=360, description="Loan tenure in months")
    primary_account_id: str = Field(..., description="Primary account ID")
    monthly_income: Optional[Decimal] = Field(None, description="Monthly income")
    existing_emi: Optional[Decimal] = Field(None, description="Existing EMI obligations")
    collateral_value: Optional[Decimal] = Field(None, description="Collateral value")
    employment_type: Optional[str] = Field(None, description="Employment type")
    employment_years: Optional[int] = Field(None, description="Years of employment")
    pan_number: Optional[str] = Field(None, description="PAN number")
    aadhar_number: Optional[str] = Field(None, description="Aadhar number")
    cibil_score: Optional[int] = Field(None, ge=300, le=900, description="CIBIL score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class LoanApprovalModel(BaseModel):
    approved_amount: Decimal = Field(..., gt=0, description="Approved amount")
    approved_tenure_months: int = Field(..., gt=0, description="Approved tenure")
    interest_rate: Decimal = Field(..., gt=0, description="Interest rate")
    processing_fee: Optional[Decimal] = Field(None, description="Processing fee")
    insurance_amount: Optional[Decimal] = Field(None, description="Insurance amount")
    approver_id: str = Field(..., description="Approver ID")
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    conditions: Optional[List[str]] = Field(None, description="Approval conditions")


class LoanDisbursementModel(BaseModel):
    disbursement_amount: Decimal = Field(..., gt=0, description="Disbursement amount")
    disbursement_account_id: str = Field(..., description="Disbursement account")
    disbursement_mode: str = Field(..., description="Disbursement mode")
    reference_number: Optional[str] = Field(None, description="Reference number")
    notes: Optional[str] = Field(None, description="Disbursement notes")


class LoanPaymentModel(BaseModel):
    payment_amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_date: date = Field(..., description="Payment date")
    payment_method: str = Field(..., description="Payment method")
    from_account_id: str = Field(..., description="Payment from account")
    transaction_reference: Optional[str] = Field(None, description="Transaction reference")
    is_prepayment: bool = Field(False, description="Is prepayment")
    notes: Optional[str] = Field(None, description="Payment notes")


class EMICalculationModel(BaseModel):
    principal_amount: Decimal = Field(..., gt=0, description="Principal amount")
    interest_rate: Decimal = Field(..., gt=0, description="Annual interest rate")
    tenure_months: int = Field(..., gt=0, description="Tenure in months")
    loan_type: str = Field(..., description="Loan type")
    processing_fee: Optional[Decimal] = Field(None, description="Processing fee")


# Router setup
router = APIRouter(prefix="/api/v2/loans", tags=["Loans V2.0"])


# Mock service dependencies
def get_loan_service():
    return {"service": "loan_service_mock"}

def get_loan_calculation_service():
    return {"service": "calculation_service_mock"}


# Loan Application Endpoints
@router.post("/applications", status_code=status.HTTP_201_CREATED)
async def create_loan_application(
    application: LoanApplicationCreateModel,
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """Create a new loan application"""
    try:
        # Mock implementation
        application_id = str(uuid.uuid4())
        return {
            "status": "success",
            "message": "Loan application created successfully",
            "data": {
                "application_id": application_id,
                "customer_id": application.customer_id,
                "loan_type": application.loan_type,
                "requested_amount": float(application.requested_amount),
                "status": "pending_review",
                "created_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create loan application: {str(e)}"
        )


@router.get("/applications/{application_id}")
async def get_loan_application(
    application_id: str,
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """Get loan application details"""
    try:
        # Mock implementation
        return {
            "status": "success",
            "data": {
                "application_id": application_id,
                "customer_id": "customer_123",
                "loan_type": "personal",
                "requested_amount": 100000.0,
                "status": "pending_review",
                "created_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve loan application: {str(e)}"
        )


@router.get("/applications")
async def list_loan_applications(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    loan_type: Optional[str] = Query(None, description="Filter by loan type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """List loan applications with filtering"""
    try:
        # Mock implementation
        return {
            "status": "success",
            "data": [
                {
                    "application_id": str(uuid.uuid4()),
                    "customer_id": customer_id or "customer_123",
                    "loan_type": loan_type or "personal",
                    "requested_amount": 100000.0,
                    "status": status or "pending_review"
                }
            ],
            "total_count": 1,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list loan applications: {str(e)}"
        )


# Loan Approval Endpoints
@router.post("/applications/{application_id}/approve")
async def approve_loan_application(
    application_id: str,
    approval: LoanApprovalModel,
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """Approve a loan application"""
    try:
        loan_id = str(uuid.uuid4())
        return {
            "status": "success",
            "message": "Loan application approved successfully",
            "data": {
                "loan_id": loan_id,
                "application_id": application_id,
                "approved_amount": float(approval.approved_amount),
                "interest_rate": float(approval.interest_rate),
                "tenure_months": approval.approved_tenure_months,
                "status": "approved",
                "approved_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to approve loan application: {str(e)}"
        )


@router.post("/applications/{application_id}/reject")
async def reject_loan_application(
    application_id: str,
    rejection_reason: str,
    rejector_id: str,
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """Reject a loan application"""
    try:
        return {
            "status": "success",
            "message": "Loan application rejected",
            "data": {
                "application_id": application_id,
                "status": "rejected",
                "rejection_reason": rejection_reason,
                "rejected_by": rejector_id,
                "rejected_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to reject loan application: {str(e)}"
        )


# Loan Disbursement Endpoints
@router.post("/loans/{loan_id}/disburse")
async def disburse_loan(
    loan_id: str,
    disbursement: LoanDisbursementModel,
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """Disburse an approved loan"""
    try:
        disbursement_id = str(uuid.uuid4())
        return {
            "status": "success",
            "message": "Loan disbursed successfully",
            "data": {
                "disbursement_id": disbursement_id,
                "loan_id": loan_id,
                "disbursement_amount": float(disbursement.disbursement_amount),
                "disbursement_account_id": disbursement.disbursement_account_id,
                "disbursement_mode": disbursement.disbursement_mode,
                "status": "disbursed",
                "disbursed_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to disburse loan: {str(e)}"
        )


# Loan Payment Endpoints
@router.post("/loans/{loan_id}/payments")
async def process_loan_payment(
    loan_id: str,
    payment: LoanPaymentModel,
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """Process a loan payment"""
    try:
        payment_id = str(uuid.uuid4())
        return {
            "status": "success",
            "message": "Loan payment processed successfully",
            "data": {
                "payment_id": payment_id,
                "loan_id": loan_id,
                "payment_amount": float(payment.payment_amount),
                "payment_date": payment.payment_date.isoformat(),
                "payment_method": payment.payment_method,
                "is_prepayment": payment.is_prepayment,
                "outstanding_balance": 50000.0,
                "processed_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process loan payment: {str(e)}"
        )


@router.get("/loans/{loan_id}/payments")
async def get_loan_payments(
    loan_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """Get loan payment history"""
    try:
        return {
            "status": "success",
            "data": [
                {
                    "payment_id": str(uuid.uuid4()),
                    "loan_id": loan_id,
                    "payment_amount": 5000.0,
                    "payment_date": datetime.utcnow().date().isoformat(),
                    "payment_method": "bank_transfer",
                    "is_prepayment": False
                }
            ],
            "total_count": 1
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve loan payments: {str(e)}"
        )


# Loan Query Endpoints
@router.get("/loans/{loan_id}")
async def get_loan_details(
    loan_id: str,
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """Get detailed loan information"""
    try:
        return {
            "status": "success",
            "data": {
                "loan_id": loan_id,
                "customer_id": "customer_123",
                "loan_type": "personal",
                "principal_amount": 100000.0,
                "interest_rate": 12.5,
                "tenure_months": 24,
                "outstanding_balance": 50000.0,
                "status": "active",
                "disbursed_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve loan details: {str(e)}"
        )


@router.get("/loans")
async def list_loans(
    customer_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    loan_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """List loans with filtering"""
    try:
        return {
            "status": "success",
            "data": [
                {
                    "loan_id": str(uuid.uuid4()),
                    "customer_id": customer_id or "customer_123",
                    "loan_type": loan_type or "personal",
                    "principal_amount": 100000.0,
                    "outstanding_balance": 50000.0,
                    "status": status or "active"
                }
            ],
            "total_count": 1
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list loans: {str(e)}"
        )


# EMI Calculation Endpoints
@router.post("/calculate/emi")
async def calculate_emi(
    calculation: EMICalculationModel,
    calc_service = Depends(get_loan_calculation_service)
) -> Dict[str, Any]:
    """Calculate EMI for given loan parameters"""
    try:
        # Simple EMI calculation: P * [r(1+r)^n] / [(1+r)^n - 1]
        principal = float(calculation.principal_amount)
        rate = float(calculation.interest_rate) / 100 / 12  # Monthly rate
        tenure = calculation.tenure_months
        
        emi = principal * (rate * (1 + rate) ** tenure) / ((1 + rate) ** tenure - 1)
        total_amount = emi * tenure
        total_interest = total_amount - principal
        
        return {
            "status": "success",
            "data": {
                "principal_amount": principal,
                "interest_rate": float(calculation.interest_rate),
                "tenure_months": tenure,
                "emi_amount": round(emi, 2),
                "total_amount": round(total_amount, 2),
                "total_interest": round(total_interest, 2),
                "processing_fee": float(calculation.processing_fee or 0)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to calculate EMI: {str(e)}"
        )


@router.get("/loans/{loan_id}/schedule")
async def get_emi_schedule(
    loan_id: str,
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """Get EMI schedule for a loan"""
    try:
        # Mock EMI schedule
        schedule = []
        for i in range(1, 25):  # 24 months
            schedule.append({
                "installment_number": i,
                "due_date": (datetime.utcnow().date().replace(day=15)).isoformat(),
                "emi_amount": 5000.0,
                "principal_component": 4000.0,
                "interest_component": 1000.0,
                "outstanding_balance": 100000.0 - (i * 4000.0),
                "status": "pending" if i > 12 else "paid"
            })
        
        return {
            "status": "success",
            "data": {
                "loan_id": loan_id,
                "schedule": schedule
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve EMI schedule: {str(e)}"
        )


# Loan Analytics Endpoints
@router.get("/analytics/portfolio")
async def get_loan_portfolio_analytics(
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """Get loan portfolio analytics"""
    try:
        return {
            "status": "success",
            "data": {
                "total_loans": 150,
                "total_disbursed_amount": 15000000.0,
                "total_outstanding": 8500000.0,
                "average_loan_size": 100000.0,
                "portfolio_yield": 12.8,
                "npa_percentage": 2.3,
                "active_loans": 142,
                "closed_loans": 8
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve portfolio analytics: {str(e)}"
        )


@router.get("/analytics/performance")
async def get_loan_performance_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    loan_service = Depends(get_loan_service)
) -> Dict[str, Any]:
    """Get loan performance analytics"""
    try:
        return {
            "status": "success",
            "data": {
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "disbursements": 25,
                "disbursed_amount": 2500000.0,
                "collections": 1800000.0,
                "collection_efficiency": 95.2,
                "new_npas": 2,
                "recovered_amount": 150000.0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance analytics: {str(e)}"
        )


# Health Check Endpoint
@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for loan service"""
    return {
        "status": "healthy",
        "service": "loan-service-v2",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }


# Export router
__all__ = ["router"]