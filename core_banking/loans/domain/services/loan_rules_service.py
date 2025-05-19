"""
Loan Rules Service

This service implements business rules for loans.
"""
from decimal import Decimal
from typing import Dict, Any, List, Optional

from ..entities.loan import LoanType, Loan

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class LoanRulesService:
    """
    Loan Rules Service
    
    This service implements business rules for loans, including eligibility,
    risk assessment, and payment calculation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Loan Rules Service
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Default configuration
        self.interest_rate_limits = self.config.get('interest_rate_limits', {
            LoanType.PERSONAL.value: Decimal('0.25'),
            LoanType.HOME.value: Decimal('0.12'),
            LoanType.AUTO.value: Decimal('0.15'),
            LoanType.EDUCATION.value: Decimal('0.08'),
            LoanType.BUSINESS.value: Decimal('0.20'),
            LoanType.SECURED.value: Decimal('0.10'),
            LoanType.UNSECURED.value: Decimal('0.25')
        })
        
        self.max_loan_amounts = self.config.get('max_loan_amounts', {
            LoanType.PERSONAL.value: Decimal('100000'),
            LoanType.HOME.value: Decimal('10000000'),
            LoanType.AUTO.value: Decimal('500000'),
            LoanType.EDUCATION.value: Decimal('500000'),
            LoanType.BUSINESS.value: Decimal('5000000'),
            LoanType.SECURED.value: Decimal('10000000'),
            LoanType.UNSECURED.value: Decimal('200000')
        })
        
        self.max_term_months = self.config.get('max_term_months', {
            LoanType.PERSONAL.value: 60,
            LoanType.HOME.value: 360,
            LoanType.AUTO.value: 84,
            LoanType.EDUCATION.value: 180,
            LoanType.BUSINESS.value: 120,
            LoanType.SECURED.value: 240,
            LoanType.UNSECURED.value: 60
        })
    
    def validate_loan_application(self, loan: Loan) -> Dict[str, str]:
        """
        Validate a loan application against business rules
        
        Args:
            loan: The loan entity to validate
            
        Returns:
            Dictionary of validation errors (empty if valid)
        """
        errors = {}
        
        # Validate loan amount
        max_amount = self.max_loan_amounts.get(loan.loan_type.value)
        if max_amount and loan.amount > max_amount:
            errors['amount'] = f"Loan amount exceeds maximum of {max_amount} for {loan.loan_type.value} loans"
        
        # Validate interest rate
        max_rate = self.interest_rate_limits.get(loan.loan_type.value)
        if max_rate and loan.terms.interest_rate > max_rate:
            errors['interest_rate'] = f"Interest rate exceeds maximum of {max_rate} for {loan.loan_type.value} loans"
        
        # Validate term months
        max_term = self.max_term_months.get(loan.loan_type.value)
        if max_term and loan.terms.term_months > max_term:
            errors['term_months'] = f"Loan term exceeds maximum of {max_term} months for {loan.loan_type.value} loans"
        
        # Validate collateral for secured loans
        if loan.loan_type == LoanType.SECURED:
            if not loan.collateral_description or not loan.collateral_value:
                errors['collateral'] = "Secured loans require collateral description and value"
            elif loan.collateral_value < (loan.amount * Decimal('0.8')):
                errors['collateral_value'] = "Collateral value must be at least 80% of the loan amount"
        
        return errors
    
    def calculate_risk_score(self, 
                            loan: Loan, 
                            customer_credit_score: int,
                            debt_to_income_ratio: Decimal) -> int:
        """
        Calculate risk score for a loan application
        
        Args:
            loan: The loan entity
            customer_credit_score: The customer's credit score (300-850)
            debt_to_income_ratio: The customer's debt-to-income ratio
            
        Returns:
            Risk score from 0-100 (higher is riskier)
        """
        # Base score from credit score (inversely proportional)
        credit_score_factor = max(0, min(100, int((850 - customer_credit_score) / 5.5)))
        
        # Debt-to-income factor (higher ratio means higher risk)
        dti_factor = min(100, int(debt_to_income_ratio * 100))
        
        # Loan type risk factor
        loan_type_risk = {
            LoanType.SECURED: 10,
            LoanType.HOME: 20,
            LoanType.AUTO: 30,
            LoanType.BUSINESS: 40,
            LoanType.EDUCATION: 40,
            LoanType.PERSONAL: 60,
            LoanType.UNSECURED: 70
        }
        
        # Amount factor (percentage of max loan amount for this type)
        max_amount = self.max_loan_amounts.get(loan.loan_type.value, Decimal('100000'))
        amount_factor = min(100, int((loan.amount / max_amount) * 100))
        
        # Term factor (percentage of max term for this type)
        max_term = self.max_term_months.get(loan.loan_type.value, 60)
        term_factor = min(100, int((loan.terms.term_months / max_term) * 100))
        
        # Weighted risk score
        risk_score = (
            (credit_score_factor * 0.4) +
            (dti_factor * 0.3) +
            (loan_type_risk.get(loan.loan_type, 50) * 0.1) +
            (amount_factor * 0.1) +
            (term_factor * 0.1)
        )
        
        return int(risk_score)
    
    def is_eligible_for_loan(self, 
                          risk_score: int, 
                          customer_credit_score: int,
                          debt_to_income_ratio: Decimal) -> bool:
        """
        Determine if a customer is eligible for a loan
        
        Args:
            risk_score: Calculated risk score (0-100)
            customer_credit_score: Customer's credit score (300-850)
            debt_to_income_ratio: Customer's debt-to-income ratio
            
        Returns:
            True if eligible, False otherwise
        """
        # Basic eligibility rules
        if risk_score > 80:
            return False
        
        if customer_credit_score < 600:
            return False
        
        if debt_to_income_ratio > Decimal('0.5'):  # 50% debt-to-income ratio
            return False
        
        return True
    
    def generate_payment_schedule(self, 
                               loan: Loan) -> List[Dict[str, Any]]:
        """
        Generate a payment schedule for a loan
        
        Args:
            loan: The loan entity
            
        Returns:
            List of payment schedule items
        """
        # This is a simplified implementation
        # A real implementation would use more complex amortization
        
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        
        payment_schedule = []
        
        # Calculate monthly payment (simple formula for demo)
        principal = loan.amount
        rate = loan.terms.interest_rate
        term = loan.terms.term_months
        
        # Convert annual rate to monthly
        monthly_rate = rate / Decimal('12')
        
        # Calculate monthly payment using amortization formula
        if monthly_rate == Decimal('0'):
            monthly_payment = principal / term
        else:
            monthly_payment = principal * (
                monthly_rate * (1 + monthly_rate) ** term) / ((1 + monthly_rate) ** term - 1
            )
        
        # Calculate start date (typically 1 month after disbursement)
        if loan.disbursal_date:
            start_date = loan.disbursal_date + relativedelta(months=1)
        else:
            # Use application date + 1 month if disbursal date is not available
            start_date = loan.application_date + relativedelta(months=1)
        
        # Generate schedule
        remaining_balance = principal
        for i in range(term):
            # Calculate interest for this period
            interest_amount = remaining_balance * monthly_rate
            
            # Calculate principal for this period
            principal_amount = monthly_payment - interest_amount
            
            # Adjust for final payment
            if i == term - 1:
                principal_amount = remaining_balance
                monthly_payment = principal_amount + interest_amount
            
            # Calculate due date based on frequency
            if loan.terms.repayment_frequency.value == 'monthly':
                due_date = start_date + relativedelta(months=i)
            elif loan.terms.repayment_frequency.value == 'quarterly':
                due_date = start_date + relativedelta(months=i * 3)
            elif loan.terms.repayment_frequency.value == 'semiannually':
                due_date = start_date + relativedelta(months=i * 6)
            elif loan.terms.repayment_frequency.value == 'annually':
                due_date = start_date + relativedelta(years=i)
            elif loan.terms.repayment_frequency.value == 'weekly':
                due_date = start_date + timedelta(weeks=i)
            elif loan.terms.repayment_frequency.value == 'biweekly':
                due_date = start_date + timedelta(weeks=i * 2)
            else:  # daily
                due_date = start_date + timedelta(days=i)
            
            # Update remaining balance
            remaining_balance -= principal_amount
            
            # Add to schedule
            payment_schedule.append({
                'due_date': due_date,
                'payment_amount': monthly_payment,
                'principal_amount': principal_amount,
                'interest_amount': interest_amount,
                'remaining_balance': max(Decimal('0'), remaining_balance),
                'is_paid': False
            })
        
        return payment_schedule
