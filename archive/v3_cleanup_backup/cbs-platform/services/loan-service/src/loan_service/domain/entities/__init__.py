"""
Loan Domain Entities

Core business entities for loan management in CBS platform.
Implements sophisticated loan products with business rules.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from platform.shared.events import DomainEvent


class LoanType(Enum):
    """Types of loans supported by the platform."""
    PERSONAL = "PERSONAL"
    HOME = "HOME"
    AUTO = "AUTO"
    BUSINESS = "BUSINESS"
    EDUCATION = "EDUCATION"
    GOLD = "GOLD"
    AGRICULTURE = "AGRICULTURE"
    OVERDRAFT = "OVERDRAFT"


class LoanStatus(Enum):
    """Loan lifecycle status."""
    APPLIED = "APPLIED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISBURSED = "DISBURSED"
    ACTIVE = "ACTIVE"
    OVERDUE = "OVERDUE"
    DEFAULTED = "DEFAULTED"
    CLOSED = "CLOSED"
    WRITTEN_OFF = "WRITTEN_OFF"


class RepaymentFrequency(Enum):
    """Loan repayment frequency options."""
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    YEARLY = "YEARLY"
    BULLET = "BULLET"  # Single payment at maturity


class InterestType(Enum):
    """Interest calculation types."""
    SIMPLE = "SIMPLE"
    COMPOUND = "COMPOUND"
    REDUCING_BALANCE = "REDUCING_BALANCE"
    FLAT_RATE = "FLAT_RATE"


class CollateralType(Enum):
    """Types of collateral for secured loans."""
    PROPERTY = "PROPERTY"
    VEHICLE = "VEHICLE"
    GOLD = "GOLD"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    SECURITIES = "SECURITIES"
    BUSINESS_ASSETS = "BUSINESS_ASSETS"


@dataclass(frozen=True)
class Money:
    """Value object representing monetary amount."""
    amount: Decimal
    currency: str = "INR"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency is required")
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)
    
    def multiply(self, factor: Decimal) -> 'Money':
        return Money(self.amount * factor, self.currency)


@dataclass
class InterestRate:
    """Interest rate specification."""
    rate: Decimal  # Annual percentage rate
    type: InterestType
    is_floating: bool = False
    base_rate: Optional[Decimal] = None  # For floating rates
    spread: Optional[Decimal] = None     # Spread over base rate
    
    def __post_init__(self):
        if self.rate < 0 or self.rate > 100:
            raise ValueError("Interest rate must be between 0 and 100")
        
        if self.is_floating and (self.base_rate is None or self.spread is None):
            raise ValueError("Floating rate requires base_rate and spread")
    
    def get_effective_rate(self, current_base_rate: Optional[Decimal] = None) -> Decimal:
        """Get the effective interest rate."""
        if self.is_floating and current_base_rate is not None:
            return current_base_rate + self.spread
        return self.rate


@dataclass
class LoanTerms:
    """Loan terms and conditions."""
    principal_amount: Money
    interest_rate: InterestRate
    tenure_months: int
    repayment_frequency: RepaymentFrequency
    processing_fee: Money
    late_payment_fee: Money
    prepayment_penalty_rate: Decimal = Decimal("0")
    grace_period_days: int = 7
    
    def __post_init__(self):
        if self.tenure_months <= 0:
            raise ValueError("Tenure must be positive")
        if self.prepayment_penalty_rate < 0 or self.prepayment_penalty_rate > 100:
            raise ValueError("Prepayment penalty rate must be between 0 and 100")
        if self.grace_period_days < 0:
            raise ValueError("Grace period cannot be negative")


@dataclass
class Collateral:
    """Collateral details for secured loans."""
    collateral_id: UUID
    type: CollateralType
    description: str
    valuation_amount: Money
    valuation_date: date
    ltv_ratio: Decimal  # Loan-to-Value ratio
    
    def __post_init__(self):
        if self.ltv_ratio <= 0 or self.ltv_ratio > 100:
            raise ValueError("LTV ratio must be between 0 and 100")


@dataclass
class RepaymentScheduleEntry:
    """Single entry in loan repayment schedule."""
    installment_number: int
    due_date: date
    principal_amount: Money
    interest_amount: Money
    total_amount: Money
    outstanding_balance: Money
    is_paid: bool = False
    paid_date: Optional[date] = None
    paid_amount: Optional[Money] = None


class LoanApplication:
    """
    Loan application aggregate root.
    
    Represents a loan application with all necessary
    information for processing and approval.
    """
    
    def __init__(
        self,
        application_id: Optional[UUID] = None,
        customer_id: UUID = None,
        loan_type: LoanType = None,
        requested_amount: Money = None
    ):
        self.application_id = application_id or uuid4()
        self.customer_id = customer_id
        self.loan_type = loan_type
        self.requested_amount = requested_amount
        self.status = LoanStatus.APPLIED
        self.applied_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.application_data: Dict[str, Any] = {}
        self.documents: List[UUID] = []
        self.credit_score: Optional[int] = None
        self.income_verification: Optional[Money] = None
        self.collateral: Optional[Collateral] = None
        self.approval_notes: Optional[str] = None
        self.rejection_reason: Optional[str] = None
        self.approved_by: Optional[UUID] = None
        self.approved_date: Optional[datetime] = None
        self.events: List[DomainEvent] = []
    
    def add_document(self, document_id: UUID) -> None:
        """Add a document to the application."""
        if document_id not in self.documents:
            self.documents.append(document_id)
            self.updated_at = datetime.utcnow()
    
    def set_credit_score(self, score: int) -> None:
        """Set the credit score for the application."""
        if score < 300 or score > 850:
            raise ValueError("Credit score must be between 300 and 850")
        self.credit_score = score
        self.updated_at = datetime.utcnow()
    
    def verify_income(self, monthly_income: Money) -> None:
        """Verify applicant's income."""
        self.income_verification = monthly_income
        self.updated_at = datetime.utcnow()
    
    def add_collateral(self, collateral: Collateral) -> None:
        """Add collateral to the application."""
        self.collateral = collateral
        self.updated_at = datetime.utcnow()
    
    def approve(self, approved_by: UUID, notes: Optional[str] = None) -> None:
        """Approve the loan application."""
        if self.status != LoanStatus.UNDER_REVIEW:
            raise ValueError("Can only approve applications under review")
        
        self.status = LoanStatus.APPROVED
        self.approved_by = approved_by
        self.approved_date = datetime.utcnow()
        self.approval_notes = notes
        self.updated_at = datetime.utcnow()
        
        # Emit domain event
        event = LoanApplicationApproved(
            application_id=self.application_id,
            customer_id=self.customer_id,
            approved_by=approved_by,
            approved_amount=self.requested_amount,
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
    
    def reject(self, rejected_by: UUID, reason: str) -> None:
        """Reject the loan application."""
        if self.status not in [LoanStatus.APPLIED, LoanStatus.UNDER_REVIEW]:
            raise ValueError("Can only reject pending applications")
        
        self.status = LoanStatus.REJECTED
        self.rejection_reason = reason
        self.updated_at = datetime.utcnow()
        
        # Emit domain event
        event = LoanApplicationRejected(
            application_id=self.application_id,
            customer_id=self.customer_id,
            rejected_by=rejected_by,
            reason=reason,
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)


class Loan:
    """
    Loan aggregate root.
    
    Represents an active loan with repayment schedule,
    payment tracking, and business rules enforcement.
    """
    
    def __init__(
        self,
        loan_id: Optional[UUID] = None,
        application_id: UUID = None,
        customer_id: UUID = None,
        account_id: UUID = None,
        loan_terms: LoanTerms = None
    ):
        self.loan_id = loan_id or uuid4()
        self.application_id = application_id
        self.customer_id = customer_id
        self.account_id = account_id
        self.loan_terms = loan_terms
        self.status = LoanStatus.APPROVED
        self.disbursed_amount: Optional[Money] = None
        self.disbursement_date: Optional[datetime] = None
        self.maturity_date: Optional[date] = None
        self.outstanding_balance: Optional[Money] = None
        self.repayment_schedule: List[RepaymentScheduleEntry] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.events: List[DomainEvent] = []
        self.is_overdue = False
        self.days_overdue = 0
    
    def disburse(self, amount: Money, disbursement_date: Optional[datetime] = None) -> None:
        """Disburse the loan amount."""
        if self.status != LoanStatus.APPROVED:
            raise ValueError("Can only disburse approved loans")
        
        if amount.amount > self.loan_terms.principal_amount.amount:
            raise ValueError("Disbursement amount cannot exceed approved amount")
        
        self.disbursed_amount = amount
        self.disbursement_date = disbursement_date or datetime.utcnow()
        self.outstanding_balance = amount
        self.status = LoanStatus.DISBURSED
        self.updated_at = datetime.utcnow()
        
        # Calculate maturity date
        from dateutil.relativedelta import relativedelta
        disbursement_date_obj = self.disbursement_date.date()
        self.maturity_date = disbursement_date_obj + relativedelta(
            months=self.loan_terms.tenure_months
        )
        
        # Generate repayment schedule
        self._generate_repayment_schedule()
        
        # Change status to active
        self.status = LoanStatus.ACTIVE
        
        # Emit domain event
        event = LoanDisbursed(
            loan_id=self.loan_id,
            customer_id=self.customer_id,
            disbursed_amount=amount,
            disbursement_date=self.disbursement_date,
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
    
    def make_payment(self, amount: Money, payment_date: Optional[date] = None) -> None:
        """Process a loan payment."""
        if self.status not in [LoanStatus.ACTIVE, LoanStatus.OVERDUE]:
            raise ValueError("Can only make payments on active loans")
        
        payment_date = payment_date or date.today()
        
        # Find the next unpaid installment
        next_installment = self._get_next_unpaid_installment()
        if not next_installment:
            raise ValueError("No pending installments")
        
        # Mark installment as paid
        next_installment.is_paid = True
        next_installment.paid_date = payment_date
        next_installment.paid_amount = amount
        
        # Update outstanding balance
        self.outstanding_balance = next_installment.outstanding_balance
        
        # Check if loan is fully paid
        if self.outstanding_balance.amount == 0:
            self.status = LoanStatus.CLOSED
        elif self.is_overdue and payment_date <= next_installment.due_date:
            self.is_overdue = False
            self.days_overdue = 0
        
        self.updated_at = datetime.utcnow()
        
        # Emit domain event
        event = LoanPaymentMade(
            loan_id=self.loan_id,
            customer_id=self.customer_id,
            payment_amount=amount,
            payment_date=payment_date,
            outstanding_balance=self.outstanding_balance,
            occurred_at=datetime.utcnow()
        )
        self.events.append(event)
    
    def mark_overdue(self) -> None:
        """Mark loan as overdue."""
        if self.status != LoanStatus.ACTIVE:
            return
        
        today = date.today()
        next_installment = self._get_next_unpaid_installment()
        
        if next_installment and today > next_installment.due_date:
            self.is_overdue = True
            self.days_overdue = (today - next_installment.due_date).days
            
            if self.days_overdue > 90:  # Default after 90 days
                self.status = LoanStatus.DEFAULTED
            else:
                self.status = LoanStatus.OVERDUE
            
            self.updated_at = datetime.utcnow()
            
            # Emit domain event
            event = LoanMarkedOverdue(
                loan_id=self.loan_id,
                customer_id=self.customer_id,
                days_overdue=self.days_overdue,
                occurred_at=datetime.utcnow()
            )
            self.events.append(event)
    
    def _generate_repayment_schedule(self) -> None:
        """Generate the loan repayment schedule."""
        if not self.disbursed_amount or not self.disbursement_date:
            raise ValueError("Loan must be disbursed before generating schedule")
        
        principal = self.disbursed_amount.amount
        annual_rate = self.loan_terms.interest_rate.get_effective_rate()
        monthly_rate = annual_rate / Decimal("100") / Decimal("12")
        tenure = self.loan_terms.tenure_months
        
        # Calculate EMI using reducing balance method
        if self.loan_terms.interest_rate.type == InterestType.REDUCING_BALANCE:
            emi = self._calculate_emi(principal, monthly_rate, tenure)
        else:
            # Simple interest calculation
            total_interest = principal * annual_rate * tenure / (Decimal("100") * Decimal("12"))
            emi = (principal + total_interest) / tenure
        
        current_date = self.disbursement_date.date()
        outstanding = principal
        
        for i in range(1, tenure + 1):
            # Calculate due date based on frequency
            if self.loan_terms.repayment_frequency == RepaymentFrequency.MONTHLY:
                from dateutil.relativedelta import relativedelta
                due_date = current_date + relativedelta(months=i)
            else:
                # Implement other frequencies as needed
                due_date = current_date + relativedelta(months=i)
            
            # Calculate interest and principal components
            if self.loan_terms.interest_rate.type == InterestType.REDUCING_BALANCE:
                interest_amount = outstanding * monthly_rate
                principal_amount = emi - interest_amount
            else:
                interest_amount = principal * monthly_rate
                principal_amount = emi - interest_amount
            
            outstanding -= principal_amount
            
            # Ensure outstanding doesn't go negative due to rounding
            if outstanding < 0:
                principal_amount += outstanding
                outstanding = Decimal("0")
            
            entry = RepaymentScheduleEntry(
                installment_number=i,
                due_date=due_date,
                principal_amount=Money(principal_amount, self.disbursed_amount.currency),
                interest_amount=Money(interest_amount, self.disbursed_amount.currency),
                total_amount=Money(emi, self.disbursed_amount.currency),
                outstanding_balance=Money(outstanding, self.disbursed_amount.currency)
            )
            
            self.repayment_schedule.append(entry)
    
    def _calculate_emi(self, principal: Decimal, monthly_rate: Decimal, tenure: int) -> Decimal:
        """Calculate EMI using the standard formula."""
        if monthly_rate == 0:
            return principal / tenure
        
        numerator = principal * monthly_rate * ((1 + monthly_rate) ** tenure)
        denominator = ((1 + monthly_rate) ** tenure) - 1
        return numerator / denominator
    
    def _get_next_unpaid_installment(self) -> Optional[RepaymentScheduleEntry]:
        """Get the next unpaid installment."""
        for entry in self.repayment_schedule:
            if not entry.is_paid:
                return entry
        return None


# Domain Events
@dataclass(frozen=True)
class LoanApplicationApproved(DomainEvent):
    """Event emitted when loan application is approved."""
    application_id: UUID
    customer_id: UUID
    approved_by: UUID
    approved_amount: Money


@dataclass(frozen=True)
class LoanApplicationRejected(DomainEvent):
    """Event emitted when loan application is rejected."""
    application_id: UUID
    customer_id: UUID
    rejected_by: UUID
    reason: str


@dataclass(frozen=True)
class LoanDisbursed(DomainEvent):
    """Event emitted when loan is disbursed."""
    loan_id: UUID
    customer_id: UUID
    disbursed_amount: Money
    disbursement_date: datetime


@dataclass(frozen=True)
class LoanPaymentMade(DomainEvent):
    """Event emitted when loan payment is made."""
    loan_id: UUID
    customer_id: UUID
    payment_amount: Money
    payment_date: date
    outstanding_balance: Money


@dataclass(frozen=True)
class LoanMarkedOverdue(DomainEvent):
    """Event emitted when loan is marked overdue."""
    loan_id: UUID
    customer_id: UUID
    days_overdue: int


# Export public interface
__all__ = [
    "LoanApplication",
    "Loan",
    "LoanType",
    "LoanStatus", 
    "RepaymentFrequency",
    "InterestType",
    "CollateralType",
    "Money",
    "InterestRate", 
    "LoanTerms",
    "Collateral",
    "RepaymentScheduleEntry",
    "LoanApplicationApproved",
    "LoanApplicationRejected",
    "LoanDisbursed",
    "LoanPaymentMade", 
    "LoanMarkedOverdue"
]
