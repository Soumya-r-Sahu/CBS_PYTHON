"""
Loan Disbursement Use Case

This module implements the business logic for disbursing an approved loan.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from ...domain.entities.loan import Loan, LoanStatus
from ..interfaces.loan_repository_interface import LoanRepositoryInterface
from ..interfaces.notification_service_interface import NotificationServiceInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class LoanDisbursementError(Exception):
    """Exception raised for errors in the loan disbursement process."""
    pass


class LoanDisbursementUseCase:
    """
    Handles the business logic for disbursing loan funds to a customer.
    
    This use case implements the process of disbursing approved loan funds,
    including validation, updating the loan status, and notifications.
    """
    
    def __init__(
        self,
        loan_repository: LoanRepositoryInterface,
        notification_service: NotificationServiceInterface
    ):
        """
        Initialize the use case with required dependencies.
        
        Args:
            loan_repository: Repository for loan data persistence
            notification_service: Service for sending notifications
        """
        self.loan_repository = loan_repository
        self.notification_service = notification_service
    
    def execute(
        self,
        loan_id: str,
        disbursed_by: str,
        account_number: str,
        reference_number: Optional[str] = None,
        disbursement_notes: Optional[str] = None
    ) -> Loan:
        """
        Disburse loan funds to the customer.
        
        Args:
            loan_id: ID of the loan to disburse
            disbursed_by: ID of the staff member who disbursed the loan
            account_number: Customer account number to receive funds
            reference_number: Reference number for the disbursement transaction
            disbursement_notes: Any notes regarding the disbursement
            
        Returns:
            The updated loan entity
            
        Raises:
            LoanDisbursementError: If loan cannot be disbursed
        """
        # Fetch the loan
        loan = self.loan_repository.get_by_id(loan_id)
        if not loan:
            raise LoanDisbursementError(f"Loan with ID {loan_id} not found")
        
        # Validate current status
        if loan.status != LoanStatus.APPROVED:
            raise LoanDisbursementError(
                f"Cannot disburse loan with status {loan.status.value}, must be APPROVED"
            )
        
        # Update loan details
        loan.status = LoanStatus.ACTIVE
        loan.disbursement_date = datetime.now().date()
        loan.disbursed_by = disbursed_by
        loan.account_number = account_number
        loan.start_date = datetime.now().date()
        
        # Set reference number if provided, otherwise use loan ID
        loan.disbursement_reference = reference_number or f"DISB-{loan.id}"
        
        # Calculate maturity date (start date + term months)
        start_date = datetime.now().date()
        loan.maturity_date = datetime(
            start_date.year + ((start_date.month + loan.terms.term_months) // 12),
            ((start_date.month + loan.terms.term_months) % 12) or 12,
            min(start_date.day, 28)  # Avoid month end issues
        ).date()
        
        if disbursement_notes:
            loan.notes = loan.notes or []
            loan.notes.append({
                "date": datetime.now().date(),
                "author": disbursed_by,
                "content": disbursement_notes,
                "type": "disbursement"
            })
        
        # Update in repository
        updated_loan = self.loan_repository.update(loan)
        
        # Send notification
        self.notification_service.send_notification(
            recipient_id=loan.customer_id,
            subject="Loan Funds Disbursed",
            message=(
                f"Your {loan.loan_type.value} loan for {loan.amount} has been disbursed "
                f"to account {account_number}. "
                f"Your first payment is due in {loan.terms.grace_period_days + 30} days. "
                f"Reference: {loan.disbursement_reference}"
            )
        )
        
        return updated_loan
        
    def calculate_repayment_schedule(self, loan: Loan) -> list:
        """
        Calculate the repayment schedule for a loan.
        
        Args:
            loan: The loan entity
            
        Returns:
            A list of payment dates and amounts
        """
        # This is a placeholder for the actual implementation
        # In a real system, this would calculate the amortization schedule
        # based on the loan amount, term, interest rate, and frequency
        
        # Example structure of the return value:
        # [
        #     {"payment_number": 1, "date": date(2023, 6, 1), "amount": Decimal("250.00"), 
        #      "principal": Decimal("200.00"), "interest": Decimal("50.00")},
        #     {"payment_number": 2, "date": date(2023, 7, 1), "amount": Decimal("250.00"),
        #      "principal": Decimal("205.00"), "interest": Decimal("45.00")},
        #     ...
        # ]
        
        # For now, we'll return an empty list
        return []
