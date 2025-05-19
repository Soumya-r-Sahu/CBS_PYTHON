"""
Loans domain entities
"""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class LoanStatus(Enum):
    """Loan status enum"""
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    DEFAULTED = "defaulted"
    CLOSED = "closed"
    DENIED = "denied"


class LoanType(Enum):
    """Loan type enum"""
    PERSONAL = "personal"
    HOME = "home"
    AUTO = "auto"
    EDUCATION = "education"
    BUSINESS = "business"
    SECURED = "secured"
    UNSECURED = "unsecured"


class RepaymentFrequency(Enum):
    """Repayment frequency enum"""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUALLY = "semiannually"
    ANNUALLY = "annually"


@dataclass
class LoanTerms:
    """Loan terms value object"""
    interest_rate: Decimal
    term_months: int
    repayment_frequency: RepaymentFrequency
    grace_period_days: int
    early_repayment_penalty: Optional[Decimal] = None
    late_payment_fee: Optional[Decimal] = None


@dataclass
class PaymentScheduleItem:
    """Payment schedule item value object"""
    due_date: date
    payment_amount: Decimal
    principal_amount: Decimal
    interest_amount: Decimal
    remaining_balance: Decimal
    is_paid: bool = False
    payment_date: Optional[date] = None
    payment_amount_received: Optional[Decimal] = None
    late_fee_applied: Optional[Decimal] = None


class Loan:
    """Loan entity"""
    
    def __init__(
        self,
        loan_id: str,
        customer_id: str,
        loan_type: LoanType,
        amount: Decimal,
        terms: LoanTerms,
        application_date: date,
        status: LoanStatus = LoanStatus.PENDING,
        approval_date: Optional[date] = None,
        disbursal_date: Optional[date] = None,
        collateral_description: Optional[str] = None,
        collateral_value: Optional[Decimal] = None,
        payment_schedule: Optional[List[PaymentScheduleItem]] = None,
        purpose: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ):
        """Initialize a loan entity"""
        self.loan_id = loan_id
        self.customer_id = customer_id
        self.loan_type = loan_type
        self.amount = amount
        self.terms = terms
        self.application_date = application_date
        self.status = status
        self.approval_date = approval_date
        self.disbursal_date = disbursal_date
        self.collateral_description = collateral_description
        self.collateral_value = collateral_value
        self.payment_schedule = payment_schedule or []
        self.purpose = purpose
        self.custom_fields = custom_fields or {}
        
        # Validate loan entity
        self._validate()
    
    def _validate(self) -> None:
        """Validate loan entity"""
        if not self.loan_id:
            raise ValueError("Loan ID is required")
        
        if not self.customer_id:
            raise ValueError("Customer ID is required")
        
        if not isinstance(self.loan_type, LoanType):
            raise ValueError("Invalid loan type")
        
        if self.amount <= Decimal('0'):
            raise ValueError("Loan amount must be greater than zero")
    
    def approve(self, approval_date: date = None) -> None:
        """
        Approve the loan.
        
        Args:
            approval_date: The approval date. Defaults to current date.
        """
        if self.status != LoanStatus.PENDING:
            raise ValueError(f"Cannot approve loan with status {self.status}")
        
        self.status = LoanStatus.APPROVED
        self.approval_date = approval_date or date.today()
    
    def deny(self) -> None:
        """Deny the loan application."""
        if self.status != LoanStatus.PENDING:
            raise ValueError(f"Cannot deny loan with status {self.status}")
        
        self.status = LoanStatus.DENIED
    
    def disburse(self, disbursal_date: date = None) -> None:
        """
        Disburse the loan amount.
        
        Args:
            disbursal_date: The disbursal date. Defaults to current date.
        """
        if self.status != LoanStatus.APPROVED:
            raise ValueError(f"Cannot disburse loan with status {self.status}")
        
        self.status = LoanStatus.ACTIVE
        self.disbursal_date = disbursal_date or date.today()
    
    def close(self) -> None:
        """Close the loan."""
        if self.status not in [LoanStatus.ACTIVE, LoanStatus.PAST_DUE]:
            raise ValueError(f"Cannot close loan with status {self.status}")
        
        # Check if all payments are made
        if not all(item.is_paid for item in self.payment_schedule):
            raise ValueError("Cannot close loan with pending payments")
        
        self.status = LoanStatus.CLOSED
    
    def set_past_due(self) -> None:
        """Set the loan as past due."""
        if self.status != LoanStatus.ACTIVE:
            raise ValueError(f"Cannot set past due for loan with status {self.status}")
        
        self.status = LoanStatus.PAST_DUE
    
    def set_defaulted(self) -> None:
        """Set the loan as defaulted."""
        if self.status not in [LoanStatus.ACTIVE, LoanStatus.PAST_DUE]:
            raise ValueError(f"Cannot set defaulted for loan with status {self.status}")
        
        self.status = LoanStatus.DEFAULTED
    
    def record_payment(self, payment_date: date, payment_amount: Decimal, schedule_index: int) -> None:
        """
        Record a payment for the loan.
        
        Args:
            payment_date: The date of payment
            payment_amount: The amount paid
            schedule_index: The index in the payment schedule
        """
        if self.status not in [LoanStatus.ACTIVE, LoanStatus.PAST_DUE]:
            raise ValueError(f"Cannot record payment for loan with status {self.status}")
        
        if schedule_index < 0 or schedule_index >= len(self.payment_schedule):
            raise ValueError(f"Invalid schedule index: {schedule_index}")
        
        payment_item = self.payment_schedule[schedule_index]
        
        # Check if already paid
        if payment_item.is_paid:
            raise ValueError(f"Payment at index {schedule_index} is already paid")
        
        # Record payment
        payment_item.is_paid = True
        payment_item.payment_date = payment_date
        payment_item.payment_amount_received = payment_amount
        
        # Calculate late fee if applicable
        if payment_date > payment_item.due_date:
            days_late = (payment_date - payment_item.due_date).days
            if days_late > self.terms.grace_period_days and self.terms.late_payment_fee:
                payment_item.late_fee_applied = self.terms.late_payment_fee
        
        # Check if loan status needs to be updated
        if all(item.is_paid for item in self.payment_schedule):
            self.close()
        elif self.status == LoanStatus.PAST_DUE:
            # Check if all past due payments are made
            past_due = False
            today = date.today()
            for item in self.payment_schedule:
                if not item.is_paid and item.due_date < today:
                    past_due = True
                    break
            if not past_due:
                self.status = LoanStatus.ACTIVE
    
    def calculate_outstanding_balance(self) -> Decimal:
        """
        Calculate the current outstanding balance of the loan.
        
        Returns:
            The outstanding balance
        """
        if self.status == LoanStatus.PENDING:
            return Decimal('0')
        
        if self.status == LoanStatus.CLOSED:
            return Decimal('0')
        
        # Find unpaid scheduled payments
        total_outstanding = Decimal('0')
        for item in self.payment_schedule:
            if not item.is_paid:
                total_outstanding += item.principal_amount
        
        return total_outstanding
    
    def calculate_total_paid(self) -> Decimal:
        """
        Calculate the total amount paid on the loan.
        
        Returns:
            The total amount paid
        """
        total_paid = Decimal('0')
        for item in self.payment_schedule:
            if item.is_paid and item.payment_amount_received:
                total_paid += item.payment_amount_received
                if item.late_fee_applied:
                    total_paid += item.late_fee_applied
        
        return total_paid
    
    def calculate_next_payment_details(self) -> Optional[Dict[str, Any]]:
        """
        Calculate the next payment details.
        
        Returns:
            A dictionary containing next payment details or None if no payments are due
        """
        if self.status not in [LoanStatus.ACTIVE, LoanStatus.PAST_DUE]:
            return None
        
        # Find the next unpaid scheduled payment
        for item in self.payment_schedule:
            if not item.is_paid:
                return {
                    "due_date": item.due_date,
                    "payment_amount": item.payment_amount,
                    "principal_amount": item.principal_amount,
                    "interest_amount": item.interest_amount,
                }
        
        return None
