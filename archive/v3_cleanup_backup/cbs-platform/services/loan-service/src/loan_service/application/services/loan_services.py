"""
Loan Service Application Services

This module contains the core business logic and use cases for the loan service,
implementing comprehensive loan management functionality including origination,
underwriting, disbursement, repayment processing, and portfolio management.
"""

import uuid
import json
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
import math

from ...infrastructure.database import (
    LoanModel, EMIScheduleModel, LoanDocumentModel, CollateralModel,
    LoanPaymentModel, LoanApplicationModel, LoanApprovalModel
)
from ...infrastructure.repositories import (
    SQLLoanRepository, SQLEMIScheduleRepository, SQLLoanDocumentRepository,
    SQLCollateralRepository, SQLLoanPaymentRepository, SQLLoanApplicationRepository
)


@dataclass
class LoanApplicationRequest:
    """Loan application request data structure"""
    customer_id: str
    loan_type: str
    loan_purpose: str
    requested_amount: Decimal
    tenure_months: int
    primary_account_id: str
    monthly_income: Optional[Decimal] = None
    existing_emi: Optional[Decimal] = None
    collateral_value: Optional[Decimal] = None
    employment_type: Optional[str] = None
    employment_years: Optional[int] = None
    pan_number: Optional[str] = None
    aadhar_number: Optional[str] = None
    cibil_score: Optional[int] = None
    co_applicant_details: Optional[Dict[str, Any]] = None
    documents: Optional[List[Dict[str, str]]] = None
    reference_contacts: Optional[List[Dict[str, str]]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LoanApprovalRequest:
    """Loan approval request data structure"""
    loan_id: str
    approved_amount: Decimal
    approved_interest_rate: Decimal
    approved_tenure_months: int
    risk_category: str
    approval_conditions: Optional[List[str]] = None
    approval_notes: Optional[str] = None
    approved_by: str = "system"
    collateral_requirements: Optional[List[Dict[str, Any]]] = None


@dataclass
class LoanDisbursementRequest:
    """Loan disbursement request data structure"""
    loan_id: str
    disbursement_amount: Decimal
    disbursement_account_id: str
    disbursement_mode: str = "NEFT"  # NEFT, RTGS, IMPS, CASH, CHEQUE
    disbursement_reference: Optional[str] = None
    disbursement_charges: Optional[Decimal] = None
    processing_fee: Optional[Decimal] = None
    insurance_premium: Optional[Decimal] = None
    other_charges: Optional[Dict[str, Decimal]] = None
    disbursed_by: str = "system"
    notes: Optional[str] = None


@dataclass
class LoanPaymentRequest:
    """Loan payment request data structure"""
    loan_id: str
    payment_amount: Decimal
    payment_date: Optional[datetime] = None
    payment_mode: str = "ONLINE"  # ONLINE, CASH, CHEQUE, DD, NEFT, UPI
    payment_reference: Optional[str] = None
    payment_account_id: Optional[str] = None
    transaction_id: Optional[str] = None
    payment_type: str = "emi"  # emi, prepayment, penalty, charges
    remarks: Optional[str] = None


@dataclass
class LoanQueryRequest:
    """Loan query request data structure"""
    customer_ids: Optional[List[str]] = None
    loan_types: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    risk_categories: Optional[List[str]] = None
    amount_range: Optional[Tuple[Decimal, Decimal]] = None
    interest_rate_range: Optional[Tuple[Decimal, Decimal]] = None
    tenure_range: Optional[Tuple[int, int]] = None
    application_date_range: Optional[Tuple[datetime, datetime]] = None
    due_date_range: Optional[Tuple[datetime, datetime]] = None
    overdue_only: Optional[bool] = None
    search_text: Optional[str] = None
    page: int = 1
    page_size: int = 50
    sort_by: str = "created_at"
    sort_order: str = "desc"


@dataclass
class ServiceResult:
    """Generic service result wrapper"""
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LoanCalculationService:
    """Service for loan calculations and financial computations"""

    @staticmethod
    def calculate_emi(principal: Decimal, rate_percent: Decimal, tenure_months: int) -> Decimal:
        """Calculate EMI using reducing balance method"""
        try:
            if tenure_months <= 0:
                return Decimal('0')
            
            monthly_rate = rate_percent / Decimal('100') / Decimal('12')
            
            if monthly_rate == 0:
                return principal / Decimal(tenure_months)
            
            # EMI = P × r × (1 + r)^n / ((1 + r)^n - 1)
            one_plus_r = Decimal('1') + monthly_rate
            one_plus_r_n = one_plus_r ** tenure_months
            
            emi = principal * monthly_rate * one_plus_r_n / (one_plus_r_n - Decimal('1'))
            return emi.quantize(Decimal('0.01'))
            
        except Exception:
            return Decimal('0')

    @staticmethod
    def generate_emi_schedule(
        principal: Decimal, 
        rate_percent: Decimal, 
        tenure_months: int,
        disbursement_date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate EMI schedule with principal and interest breakdown"""
        schedule = []
        balance = principal
        monthly_rate = rate_percent / Decimal('100') / Decimal('12')
        emi = LoanCalculationService.calculate_emi(principal, rate_percent, tenure_months)
        
        current_date = disbursement_date
        
        for month in range(1, tenure_months + 1):
            # Calculate due date (usually 1st of next month)
            if current_date.day > 28:
                # Handle end of month edge cases
                next_month = current_date.replace(day=1) + timedelta(days=32)
                due_date = next_month.replace(day=1)
            else:
                try:
                    due_date = current_date.replace(month=current_date.month + 1)
                except ValueError:
                    # Year rollover
                    due_date = current_date.replace(year=current_date.year + 1, month=1)
            
            # Calculate interest and principal components
            interest_amount = (balance * monthly_rate).quantize(Decimal('0.01'))
            principal_amount = emi - interest_amount
            
            # Adjust for final payment
            if month == tenure_months:
                principal_amount = balance
                emi = principal_amount + interest_amount
            
            balance -= principal_amount
            
            schedule.append({
                'installment_number': month,
                'due_date': due_date,
                'emi_amount': emi,
                'principal_amount': principal_amount,
                'interest_amount': interest_amount,
                'balance_amount': balance,
                'status': 'pending'
            })
            
            current_date = due_date
        
        return schedule

    @staticmethod
    def calculate_prepayment_amount(
        outstanding_balance: Decimal,
        prepayment_charges_percent: Decimal = Decimal('2.0')
    ) -> Dict[str, Decimal]:
        """Calculate prepayment amount including charges"""
        prepayment_charges = (outstanding_balance * prepayment_charges_percent / Decimal('100')).quantize(Decimal('0.01'))
        total_amount = outstanding_balance + prepayment_charges
        
        return {
            'outstanding_balance': outstanding_balance,
            'prepayment_charges': prepayment_charges,
            'total_prepayment_amount': total_amount
        }

    @staticmethod
    def calculate_penalty(overdue_amount: Decimal, days_overdue: int, penalty_rate: Decimal = Decimal('2.0')) -> Decimal:
        """Calculate penalty for overdue payments"""
        if days_overdue <= 0 or overdue_amount <= 0:
            return Decimal('0')
        
        # Penalty = (Overdue Amount × Penalty Rate × Days) / (100 × 365)
        penalty = (overdue_amount * penalty_rate * Decimal(days_overdue)) / (Decimal('100') * Decimal('365'))
        return penalty.quantize(Decimal('0.01'))


class LoanUnderwritingService:
    """Service for loan underwriting and risk assessment"""

    @staticmethod
    def assess_loan_risk(
        loan_amount: Decimal,
        monthly_income: Decimal,
        existing_emi: Decimal,
        credit_score: Optional[int] = None,
        employment_years: Optional[int] = None,
        collateral_value: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Comprehensive loan risk assessment"""
        
        # Calculate debt-to-income ratio
        proposed_emi = LoanCalculationService.calculate_emi(loan_amount, Decimal('12.0'), 60)  # Assume 12% for DTI calc
        total_emi = existing_emi + proposed_emi
        dti_ratio = (total_emi / monthly_income) if monthly_income > 0 else Decimal('100')
        
        # Risk scoring factors
        risk_score = 0
        risk_factors = []
        
        # DTI ratio assessment
        if dti_ratio > Decimal('0.50'):
            risk_score += 40
            risk_factors.append("High debt-to-income ratio")
        elif dti_ratio > Decimal('0.35'):
            risk_score += 20
            risk_factors.append("Moderate debt-to-income ratio")
        elif dti_ratio <= Decimal('0.25'):
            risk_score -= 10  # Bonus for low DTI
        
        # Credit score assessment
        if credit_score:
            if credit_score < 650:
                risk_score += 35
                risk_factors.append("Poor credit score")
            elif credit_score < 700:
                risk_score += 15
                risk_factors.append("Fair credit score")
            elif credit_score >= 750:
                risk_score -= 15  # Bonus for excellent credit
        else:
            risk_score += 25
            risk_factors.append("No credit score available")
        
        # Employment stability
        if employment_years:
            if employment_years < 1:
                risk_score += 20
                risk_factors.append("Short employment history")
            elif employment_years >= 5:
                risk_score -= 10  # Bonus for stable employment
        
        # Collateral assessment
        if collateral_value and loan_amount > 0:
            ltv_ratio = loan_amount / collateral_value
            if ltv_ratio > Decimal('0.90'):
                risk_score += 15
                risk_factors.append("High loan-to-value ratio")
            elif ltv_ratio <= Decimal('0.70'):
                risk_score -= 5  # Bonus for good collateral coverage
        
        # Loan amount assessment
        if loan_amount > monthly_income * 60:  # More than 5 years of income
            risk_score += 25
            risk_factors.append("High loan amount relative to income")
        
        # Determine risk category
        risk_category = "low"
        if risk_score >= 60:
            risk_category = "very_high"
        elif risk_score >= 40:
            risk_category = "high"
        elif risk_score >= 20:
            risk_category = "medium"
        
        # Calculate recommended interest rate
        base_rate = Decimal('10.0')  # Base rate
        risk_premium = max(Decimal('0'), Decimal(str(risk_score)) * Decimal('0.1'))
        recommended_rate = base_rate + risk_premium
        
        return {
            'risk_score': risk_score,
            'risk_category': risk_category,
            'risk_factors': risk_factors,
            'dti_ratio': float(dti_ratio),
            'recommended_interest_rate': float(recommended_rate),
            'approval_recommendation': risk_category in ['low', 'medium'],
            'conditions': [
                "Income verification required",
                "Employment verification required",
                "Property valuation required" if collateral_value else "Additional security required"
            ]
        }


class CreateLoanApplicationUseCase:
    """Use case for creating new loan applications"""

    def __init__(self, 
                 loan_repository: SQLLoanRepository,
                 application_repository: SQLLoanApplicationRepository,
                 document_repository: SQLLoanDocumentRepository):
        self.loan_repository = loan_repository
        self.application_repository = application_repository
        self.document_repository = document_repository
        self.underwriting_service = LoanUnderwritingService()

    async def execute(self, request: LoanApplicationRequest) -> ServiceResult:
        """Execute loan application creation"""
        try:
            # Validate request
            validation_result = self._validate_application(request)
            if not validation_result['valid']:
                return ServiceResult(
                    success=False,
                    error_message=validation_result['message'],
                    error_code="VALIDATION_ERROR"
                )

            # Generate loan number
            loan_number = self._generate_loan_number()

            # Perform risk assessment
            risk_assessment = self.underwriting_service.assess_loan_risk(
                loan_amount=request.requested_amount,
                monthly_income=request.monthly_income or Decimal('0'),
                existing_emi=request.existing_emi or Decimal('0'),
                credit_score=request.cibil_score,
                employment_years=request.employment_years,
                collateral_value=request.collateral_value
            )

            # Create loan application
            loan_application = LoanApplicationModel(
                application_id=uuid.uuid4(),
                customer_id=uuid.UUID(request.customer_id),
                loan_type=request.loan_type,
                loan_purpose=request.loan_purpose,
                requested_amount=request.requested_amount,
                tenure_months=request.tenure_months,
                primary_account_id=uuid.UUID(request.primary_account_id),
                monthly_income=request.monthly_income,
                existing_emi=request.existing_emi,
                collateral_value=request.collateral_value,
                employment_type=request.employment_type,
                employment_years=request.employment_years,
                pan_number=request.pan_number,
                aadhar_number=request.aadhar_number,
                cibil_score=request.cibil_score,
                co_applicant_details=request.co_applicant_details,
                reference_contacts=request.reference_contacts,
                risk_assessment=risk_assessment,
                status='submitted',
                application_date=datetime.utcnow(),
                created_by='customer',
                metadata=request.metadata or {}
            )

            # Save application
            application_result = await self.application_repository.create(loan_application)
            if not application_result.success:
                return ServiceResult(
                    success=False,
                    error_message="Failed to save loan application",
                    error_code="SAVE_ERROR"
                )

            # Create loan record in draft status
            loan = LoanModel(
                loan_id=uuid.uuid4(),
                loan_number=loan_number,
                customer_id=uuid.UUID(request.customer_id),
                primary_account_id=uuid.UUID(request.primary_account_id),
                loan_type=request.loan_type,
                loan_purpose=request.loan_purpose,
                loan_amount=request.requested_amount,
                interest_rate=Decimal(str(risk_assessment['recommended_interest_rate'])),
                tenure_months=request.tenure_months,
                status='submitted',
                risk_category=risk_assessment['risk_category'],
                credit_score=request.cibil_score,
                debt_to_income_ratio=Decimal(str(risk_assessment['dti_ratio'])),
                application_date=datetime.utcnow(),
                created_by='customer',
                metadata={
                    'application_id': str(application_result.data.application_id),
                    'risk_assessment': risk_assessment,
                    **(request.metadata or {})
                }
            )

            # Save loan
            loan_result = await self.loan_repository.create(loan)
            if not loan_result.success:
                return ServiceResult(
                    success=False,
                    error_message="Failed to create loan record",
                    error_code="SAVE_ERROR"
                )

            # Save documents if provided
            if request.documents:
                for doc in request.documents:
                    document = LoanDocumentModel(
                        document_id=uuid.uuid4(),
                        loan_id=loan.loan_id,
                        document_type=doc.get('type'),
                        document_name=doc.get('name'),
                        document_url=doc.get('url'),
                        document_size=doc.get('size'),
                        upload_date=datetime.utcnow(),
                        uploaded_by='customer',
                        status='uploaded'
                    )
                    await self.document_repository.create(document)

            return ServiceResult(
                success=True,
                data={
                    'loan': loan_result.data,
                    'application': application_result.data,
                    'risk_assessment': risk_assessment
                },
                metadata={
                    'loan_id': str(loan.loan_id),
                    'loan_number': loan_number,
                    'application_id': str(application_result.data.application_id)
                }
            )

        except Exception as e:
            return ServiceResult(
                success=False,
                error_message=f"Failed to create loan application: {str(e)}",
                error_code="SYSTEM_ERROR"
            )

    def _validate_application(self, request: LoanApplicationRequest) -> Dict[str, Any]:
        """Validate loan application request"""
        if not request.customer_id:
            return {'valid': False, 'message': 'Customer ID is required'}
        
        if not request.loan_type:
            return {'valid': False, 'message': 'Loan type is required'}
        
        if not request.requested_amount or request.requested_amount <= 0:
            return {'valid': False, 'message': 'Valid loan amount is required'}
        
        if not request.tenure_months or request.tenure_months <= 0:
            return {'valid': False, 'message': 'Valid tenure is required'}
        
        if request.tenure_months > 360:  # 30 years max
            return {'valid': False, 'message': 'Maximum tenure is 30 years'}
        
        if request.requested_amount > Decimal('10000000'):  # 1 crore max
            return {'valid': False, 'message': 'Maximum loan amount is ₹1 crore'}
        
        return {'valid': True, 'message': 'Valid application'}

    def _generate_loan_number(self) -> str:
        """Generate unique loan number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"LN{timestamp}{random_suffix}"


class ApproveLoanUseCase:
    """Use case for loan approval processing"""

    def __init__(self, 
                 loan_repository: SQLLoanRepository,
                 emi_repository: SQLEMIScheduleRepository):
        self.loan_repository = loan_repository
        self.emi_repository = emi_repository
        self.calculation_service = LoanCalculationService()

    async def execute(self, request: LoanApprovalRequest) -> ServiceResult:
        """Execute loan approval"""
        try:
            # Get loan
            loan_result = await self.loan_repository.get_by_id(request.loan_id)
            if not loan_result.success:
                return ServiceResult(
                    success=False,
                    error_message="Loan not found",
                    error_code="NOT_FOUND"
                )

            loan = loan_result.data

            # Validate loan status
            if loan.status not in ['submitted', 'under_review']:
                return ServiceResult(
                    success=False,
                    error_message=f"Cannot approve loan in {loan.status} status",
                    error_code="INVALID_STATUS"
                )

            # Calculate EMI
            emi_amount = self.calculation_service.calculate_emi(
                request.approved_amount,
                request.approved_interest_rate,
                request.approved_tenure_months
            )

            # Calculate maturity date
            maturity_date = datetime.utcnow() + timedelta(days=request.approved_tenure_months * 30)

            # Update loan
            loan.approved_amount = request.approved_amount
            loan.interest_rate = request.approved_interest_rate
            loan.tenure_months = request.approved_tenure_months
            loan.emi_amount = emi_amount
            loan.status = 'approved'
            loan.risk_category = request.risk_category
            loan.approval_date = datetime.utcnow()
            loan.maturity_date = maturity_date
            loan.approved_by = request.approved_by
            loan.notes = request.approval_notes
            loan.updated_at = datetime.utcnow()

            # Add approval conditions to metadata
            if request.approval_conditions:
                loan.metadata = loan.metadata or {}
                loan.metadata['approval_conditions'] = request.approval_conditions

            # Save loan
            update_result = await self.loan_repository.update(loan)
            if not update_result.success:
                return ServiceResult(
                    success=False,
                    error_message="Failed to update loan",
                    error_code="UPDATE_ERROR"
                )

            # Generate EMI schedule
            emi_schedule = self.calculation_service.generate_emi_schedule(
                request.approved_amount,
                request.approved_interest_rate,
                request.approved_tenure_months,
                datetime.utcnow()
            )

            # Save EMI schedule
            for schedule_item in emi_schedule:
                emi_record = EMIScheduleModel(
                    schedule_id=uuid.uuid4(),
                    loan_id=loan.loan_id,
                    installment_number=schedule_item['installment_number'],
                    due_date=schedule_item['due_date'],
                    emi_amount=schedule_item['emi_amount'],
                    principal_amount=schedule_item['principal_amount'],
                    interest_amount=schedule_item['interest_amount'],
                    balance_amount=schedule_item['balance_amount'],
                    status='pending'
                )
                await self.emi_repository.create(emi_record)

            return ServiceResult(
                success=True,
                data={
                    'loan': update_result.data,
                    'emi_schedule': emi_schedule
                },
                metadata={
                    'approved_amount': float(request.approved_amount),
                    'emi_amount': float(emi_amount),
                    'total_installments': request.approved_tenure_months
                }
            )

        except Exception as e:
            return ServiceResult(
                success=False,
                error_message=f"Failed to approve loan: {str(e)}",
                error_code="SYSTEM_ERROR"
            )


class DisburseLoanUseCase:
    """Use case for loan disbursement processing"""

    def __init__(self, loan_repository: SQLLoanRepository):
        self.loan_repository = loan_repository

    async def execute(self, request: LoanDisbursementRequest) -> ServiceResult:
        """Execute loan disbursement"""
        try:
            # Get loan
            loan_result = await self.loan_repository.get_by_id(request.loan_id)
            if not loan_result.success:
                return ServiceResult(
                    success=False,
                    error_message="Loan not found",
                    error_code="NOT_FOUND"
                )

            loan = loan_result.data

            # Validate loan status
            if loan.status != 'approved':
                return ServiceResult(
                    success=False,
                    error_message=f"Cannot disburse loan in {loan.status} status",
                    error_code="INVALID_STATUS"
                )

            # Validate disbursement amount
            if request.disbursement_amount > loan.approved_amount:
                return ServiceResult(
                    success=False,
                    error_message="Disbursement amount exceeds approved amount",
                    error_code="INVALID_AMOUNT"
                )

            # Calculate net disbursement
            total_charges = (request.disbursement_charges or Decimal('0')) + \
                          (request.processing_fee or Decimal('0')) + \
                          (request.insurance_premium or Decimal('0'))
            
            if request.other_charges:
                total_charges += sum(request.other_charges.values())

            net_disbursement = request.disbursement_amount - total_charges

            # Update loan
            loan.disbursed_amount = request.disbursement_amount
            loan.outstanding_amount = request.disbursement_amount
            loan.status = 'disbursed'
            loan.disbursement_date = datetime.utcnow()
            loan.next_due_date = datetime.utcnow() + timedelta(days=30)  # First EMI due in 30 days
            loan.updated_at = datetime.utcnow()

            # Add disbursement details to metadata
            loan.metadata = loan.metadata or {}
            loan.metadata.update({
                'disbursement_details': {
                    'disbursement_account_id': request.disbursement_account_id,
                    'disbursement_mode': request.disbursement_mode,
                    'disbursement_reference': request.disbursement_reference,
                    'total_charges': float(total_charges),
                    'net_disbursement': float(net_disbursement),
                    'disbursed_by': request.disbursed_by,
                    'disbursement_timestamp': datetime.utcnow().isoformat()
                }
            })

            # Save loan
            update_result = await self.loan_repository.update(loan)
            if not update_result.success:
                return ServiceResult(
                    success=False,
                    error_message="Failed to update loan",
                    error_code="UPDATE_ERROR"
                )

            return ServiceResult(
                success=True,
                data=update_result.data,
                metadata={
                    'disbursed_amount': float(request.disbursement_amount),
                    'net_disbursement': float(net_disbursement),
                    'total_charges': float(total_charges),
                    'first_emi_due_date': loan.next_due_date.isoformat()
                }
            )

        except Exception as e:
            return ServiceResult(
                success=False,
                error_message=f"Failed to disburse loan: {str(e)}",
                error_code="SYSTEM_ERROR"
            )


class ProcessLoanPaymentUseCase:
    """Use case for processing loan payments"""

    def __init__(self, 
                 loan_repository: SQLLoanRepository,
                 payment_repository: SQLLoanPaymentRepository,
                 emi_repository: SQLEMIScheduleRepository):
        self.loan_repository = loan_repository
        self.payment_repository = payment_repository
        self.emi_repository = emi_repository
        self.calculation_service = LoanCalculationService()

    async def execute(self, request: LoanPaymentRequest) -> ServiceResult:
        """Execute loan payment processing"""
        try:
            # Get loan
            loan_result = await self.loan_repository.get_by_id(request.loan_id)
            if not loan_result.success:
                return ServiceResult(
                    success=False,
                    error_message="Loan not found",
                    error_code="NOT_FOUND"
                )

            loan = loan_result.data

            # Validate loan status
            if loan.status not in ['disbursed', 'active']:
                return ServiceResult(
                    success=False,
                    error_message=f"Cannot process payment for loan in {loan.status} status",
                    error_code="INVALID_STATUS"
                )

            # Process payment based on type
            payment_date = request.payment_date or datetime.utcnow()
            
            if request.payment_type == 'emi':
                result = await self._process_emi_payment(loan, request.payment_amount, payment_date)
            elif request.payment_type == 'prepayment':
                result = await self._process_prepayment(loan, request.payment_amount, payment_date)
            else:
                result = await self._process_other_payment(loan, request.payment_amount, request.payment_type, payment_date)

            if not result['success']:
                return ServiceResult(success=False, error_message=result['message'])

            # Create payment record
            payment = LoanPaymentModel(
                payment_id=uuid.uuid4(),
                loan_id=loan.loan_id,
                payment_amount=request.payment_amount,
                payment_date=payment_date,
                payment_mode=request.payment_mode,
                payment_reference=request.payment_reference,
                payment_account_id=uuid.UUID(request.payment_account_id) if request.payment_account_id else None,
                transaction_id=request.transaction_id,
                payment_type=request.payment_type,
                principal_amount=result.get('principal_amount', Decimal('0')),
                interest_amount=result.get('interest_amount', Decimal('0')),
                penalty_amount=result.get('penalty_amount', Decimal('0')),
                charges_amount=result.get('charges_amount', Decimal('0')),
                status='completed',
                processed_by='system',
                remarks=request.remarks
            )

            # Save payment
            payment_result = await self.payment_repository.create(payment)
            if not payment_result.success:
                return ServiceResult(
                    success=False,
                    error_message="Failed to save payment record",
                    error_code="SAVE_ERROR"
                )

            # Update loan
            loan.outstanding_amount -= result.get('principal_amount', Decimal('0'))
            loan.total_amount_paid += request.payment_amount
            loan.total_payments_made += 1
            loan.last_payment_date = payment_date
            loan.updated_at = datetime.utcnow()

            # Check if loan is fully paid
            if loan.outstanding_amount <= Decimal('0.01'):  # Account for rounding
                loan.status = 'completed'
                loan.outstanding_amount = Decimal('0')

            # Save loan
            await self.loan_repository.update(loan)

            return ServiceResult(
                success=True,
                data={
                    'payment': payment_result.data,
                    'loan': loan,
                    'payment_breakdown': result
                },
                metadata={
                    'remaining_balance': float(loan.outstanding_amount),
                    'total_paid': float(loan.total_amount_paid),
                    'loan_status': loan.status
                }
            )

        except Exception as e:
            return ServiceResult(
                success=False,
                error_message=f"Failed to process payment: {str(e)}",
                error_code="SYSTEM_ERROR"
            )

    async def _process_emi_payment(self, loan: LoanModel, amount: Decimal, payment_date: datetime) -> Dict[str, Any]:
        """Process EMI payment"""
        try:
            # Get next pending EMI
            next_emi_result = await self.emi_repository.get_next_pending_emi(loan.loan_id)
            if not next_emi_result.success:
                return {'success': False, 'message': 'No pending EMI found'}

            emi = next_emi_result.data

            # Calculate penalty if overdue
            penalty_amount = Decimal('0')
            if payment_date.date() > emi.due_date.date():
                days_overdue = (payment_date.date() - emi.due_date.date()).days
                penalty_amount = self.calculation_service.calculate_penalty(
                    emi.emi_amount, days_overdue
                )

            # Validate payment amount
            total_due = emi.emi_amount + penalty_amount
            if amount < total_due:
                return {
                    'success': False,
                    'message': f'Insufficient payment. Required: {total_due}, Provided: {amount}'
                }

            # Update EMI status
            emi.status = 'paid'
            emi.paid_date = payment_date
            emi.paid_amount = emi.emi_amount
            await self.emi_repository.update(emi)

            # Update loan next due date
            next_emi_result = await self.emi_repository.get_next_pending_emi(loan.loan_id)
            if next_emi_result.success:
                loan.next_due_date = next_emi_result.data.due_date
            else:
                loan.next_due_date = None  # All EMIs paid

            return {
                'success': True,
                'principal_amount': emi.principal_amount,
                'interest_amount': emi.interest_amount,
                'penalty_amount': penalty_amount,
                'charges_amount': Decimal('0'),
                'excess_amount': amount - total_due
            }

        except Exception as e:
            return {'success': False, 'message': f'EMI processing failed: {str(e)}'}

    async def _process_prepayment(self, loan: LoanModel, amount: Decimal, payment_date: datetime) -> Dict[str, Any]:
        """Process prepayment"""
        try:
            # Calculate prepayment details
            prepayment_calc = self.calculation_service.calculate_prepayment_amount(loan.outstanding_amount)
            
            if amount < prepayment_calc['total_prepayment_amount']:
                return {
                    'success': False,
                    'message': f'Insufficient prepayment. Required: {prepayment_calc["total_prepayment_amount"]}'
                }

            return {
                'success': True,
                'principal_amount': prepayment_calc['outstanding_balance'],
                'interest_amount': Decimal('0'),
                'penalty_amount': Decimal('0'),
                'charges_amount': prepayment_calc['prepayment_charges']
            }

        except Exception as e:
            return {'success': False, 'message': f'Prepayment processing failed: {str(e)}'}

    async def _process_other_payment(self, loan: LoanModel, amount: Decimal, payment_type: str, payment_date: datetime) -> Dict[str, Any]:
        """Process other types of payments (penalty, charges, etc.)"""
        return {
            'success': True,
            'principal_amount': Decimal('0'),
            'interest_amount': Decimal('0'),
            'penalty_amount': amount if payment_type == 'penalty' else Decimal('0'),
            'charges_amount': amount if payment_type == 'charges' else Decimal('0')
        }


class LoanQueryUseCase:
    """Use case for querying loans"""

    def __init__(self, loan_repository: SQLLoanRepository):
        self.loan_repository = loan_repository

    async def execute(self, request: LoanQueryRequest) -> ServiceResult:
        """Execute loan query"""
        try:
            result = await self.loan_repository.query_loans(
                customer_ids=request.customer_ids,
                loan_types=request.loan_types,
                statuses=request.statuses,
                risk_categories=request.risk_categories,
                amount_range=request.amount_range,
                interest_rate_range=request.interest_rate_range,
                tenure_range=request.tenure_range,
                application_date_range=request.application_date_range,
                due_date_range=request.due_date_range,
                overdue_only=request.overdue_only,
                search_text=request.search_text,
                page=request.page,
                page_size=request.page_size,
                sort_by=request.sort_by,
                sort_order=request.sort_order
            )

            return result

        except Exception as e:
            return ServiceResult(
                success=False,
                error_message=f"Failed to query loans: {str(e)}",
                error_code="QUERY_ERROR"
            )


class LoanService:
    """Main loan service orchestrating all loan operations"""

    def __init__(self,
                 loan_repository: SQLLoanRepository,
                 application_repository: SQLLoanApplicationRepository,
                 emi_repository: SQLEMIScheduleRepository,
                 document_repository: SQLLoanDocumentRepository,
                 payment_repository: SQLLoanPaymentRepository,
                 collateral_repository: SQLCollateralRepository):
        
        self.loan_repository = loan_repository
        self.application_repository = application_repository
        self.emi_repository = emi_repository
        self.document_repository = document_repository
        self.payment_repository = payment_repository
        self.collateral_repository = collateral_repository

        # Initialize use cases
        self.create_application_use_case = CreateLoanApplicationUseCase(
            loan_repository, application_repository, document_repository
        )
        self.approve_loan_use_case = ApproveLoanUseCase(loan_repository, emi_repository)
        self.disburse_loan_use_case = DisburseLoanUseCase(loan_repository)
        self.process_payment_use_case = ProcessLoanPaymentUseCase(
            loan_repository, payment_repository, emi_repository
        )
        self.query_loans_use_case = LoanQueryUseCase(loan_repository)

    async def create_loan_application(self, request: LoanApplicationRequest) -> ServiceResult:
        """Create new loan application"""
        return await self.create_application_use_case.execute(request)

    async def approve_loan(self, request: LoanApprovalRequest) -> ServiceResult:
        """Approve loan application"""
        return await self.approve_loan_use_case.execute(request)

    async def disburse_loan(self, request: LoanDisbursementRequest) -> ServiceResult:
        """Disburse approved loan"""
        return await self.disburse_loan_use_case.execute(request)

    async def process_payment(self, request: LoanPaymentRequest) -> ServiceResult:
        """Process loan payment"""
        return await self.process_payment_use_case.execute(request)

    async def query_loans(self, request: LoanQueryRequest) -> ServiceResult:
        """Query loans with filters"""
        return await self.query_loans_use_case.execute(request)

    async def get_loan_by_id(self, loan_id: str) -> ServiceResult:
        """Get loan by ID"""
        return await self.loan_repository.get_by_id(loan_id)

    async def get_emi_schedule(self, loan_id: str) -> ServiceResult:
        """Get EMI schedule for loan"""
        return await self.emi_repository.get_by_loan_id(loan_id)

    async def get_payment_history(self, loan_id: str) -> ServiceResult:
        """Get payment history for loan"""
        return await self.payment_repository.get_by_loan_id(loan_id)

    async def calculate_emi(self, principal: Decimal, rate: Decimal, tenure: int) -> Dict[str, Any]:
        """Calculate EMI for given parameters"""
        emi = LoanCalculationService.calculate_emi(principal, rate, tenure)
        total_amount = emi * tenure
        total_interest = total_amount - principal
        
        return {
            'emi_amount': float(emi),
            'total_amount': float(total_amount),
            'total_interest': float(total_interest),
            'principal': float(principal),
            'interest_rate': float(rate),
            'tenure_months': tenure
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Check database connectivity
            test_result = await self.loan_repository.health_check()
            
            return {
                'status': 'healthy' if test_result.success else 'unhealthy',
                'database_status': 'connected' if test_result.success else 'disconnected',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '2.0.0',
                'service_dependencies': {
                    'database': 'healthy' if test_result.success else 'unhealthy',
                    'calculation_service': 'healthy',
                    'underwriting_service': 'healthy'
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Export main components
__all__ = [
    'LoanService',
    'CreateLoanApplicationUseCase',
    'ApproveLoanUseCase', 
    'DisburseLoanUseCase',
    'ProcessLoanPaymentUseCase',
    'LoanQueryUseCase',
    'LoanCalculationService',
    'LoanUnderwritingService',
    'LoanApplicationRequest',
    'LoanApprovalRequest',
    'LoanDisbursementRequest',
    'LoanPaymentRequest',
    'LoanQueryRequest',
    'ServiceResult'
]
