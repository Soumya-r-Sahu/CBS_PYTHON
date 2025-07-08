"""
Loans module for the Core Banking System.

This module handles all loan-related operations, including:
- Loan origination
- EMI calculation
- Non-performing assets management
"""

from .domain.entities.loan import Loan, LoanType, LoanStatus, LoanTerms, RepaymentFrequency
from .application.use_cases.loan_application_use_case import LoanApplicationUseCase
from .application.use_cases.loan_approval_use_case import LoanApprovalUseCase
from .application.use_cases.loan_disbursement_use_case import LoanDisbursementUseCase
from .application.services.loan_calculator_service import LoanCalculatorService
from .presentation.cli import loan_cli
from .presentation.api import loan_router

__all__ = [
    # Domain entities
    'Loan',
    'LoanType',
    'LoanStatus',
    'LoanTerms',
    'RepaymentFrequency',
    
    # Application layer
    'LoanApplicationUseCase',
    'LoanApprovalUseCase',
    'LoanDisbursementUseCase',
    'LoanCalculatorService',
    
    # Presentation layer
    'loan_cli',
    'loan_router',
]
