"""
Loan Approval Use Case

This module implements the business logic for approving or denying a loan application.
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



class LoanApprovalError(Exception):
    """Exception raised for errors in the loan approval process."""
    pass


class LoanApprovalUseCase:
    """
    Handles the business logic for approving or denying a loan application.
    
    This use case implements the decision process for loan applications,
    including approval, denial, and notification of the customer.
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
    
    def approve(
        self,
        loan_id: str,
        approved_by: str,
        approved_amount: Optional[Decimal] = None,
        approved_interest_rate: Optional[Decimal] = None,
        approval_notes: Optional[str] = None
    ) -> Loan:
        """
        Approve a loan application.
        
        Args:
            loan_id: ID of the loan to approve
            approved_by: ID of the staff member who approved the loan
            approved_amount: The approved loan amount (if different from requested)
            approved_interest_rate: The approved interest rate (if different from requested)
            approval_notes: Any notes regarding the approval
            
        Returns:
            The updated loan entity
            
        Raises:
            LoanApprovalError: If loan cannot be approved
        """
        # Fetch the loan
        loan = self.loan_repository.get_by_id(loan_id)
        if not loan:
            raise LoanApprovalError(f"Loan with ID {loan_id} not found")
        
        # Validate current status
        if loan.status != LoanStatus.PENDING:
            raise LoanApprovalError(
                f"Cannot approve loan with status {loan.status.value}, must be PENDING"
            )
        
        # Update loan details
        loan.status = LoanStatus.APPROVED
        loan.approved_date = datetime.now().date()
        loan.approved_by = approved_by
        
        if approved_amount is not None:
            if approved_amount <= Decimal("0"):
                raise LoanApprovalError("Approved amount must be positive")
            loan.amount = approved_amount
        
        if approved_interest_rate is not None:
            if approved_interest_rate < Decimal("0"):
                raise LoanApprovalError("Approved interest rate cannot be negative")
            loan.terms.interest_rate = approved_interest_rate
        
        if approval_notes:
            loan.notes = loan.notes or []
            loan.notes.append({
                "date": datetime.now().date(),
                "author": approved_by,
                "content": approval_notes,
                "type": "approval"
            })
        
        # Update in repository
        updated_loan = self.loan_repository.update(loan)
        
        # Send notification
        self.notification_service.send_notification(
            recipient_id=loan.customer_id,
            subject="Loan Application Approved",
            message=(
                f"Congratulations! Your application for a {loan.loan_type.value} loan "
                f"of {loan.amount} has been approved. "
                f"Please contact our loan department for next steps."
            )
        )
        
        return updated_loan
    
    def deny(
        self,
        loan_id: str,
        denied_by: str,
        denial_reason: str,
        denial_notes: Optional[str] = None
    ) -> Loan:
        """
        Deny a loan application.
        
        Args:
            loan_id: ID of the loan to deny
            denied_by: ID of the staff member who denied the loan
            denial_reason: Reason for denial
            denial_notes: Any additional notes regarding the denial
            
        Returns:
            The updated loan entity
            
        Raises:
            LoanApprovalError: If loan cannot be denied
        """
        # Fetch the loan
        loan = self.loan_repository.get_by_id(loan_id)
        if not loan:
            raise LoanApprovalError(f"Loan with ID {loan_id} not found")
        
        # Validate current status
        if loan.status != LoanStatus.PENDING:
            raise LoanApprovalError(
                f"Cannot deny loan with status {loan.status.value}, must be PENDING"
            )
        
        # Update loan details
        loan.status = LoanStatus.DENIED
        loan.denial_date = datetime.now().date()
        loan.denied_by = denied_by
        loan.denial_reason = denial_reason
        
        if denial_notes:
            loan.notes = loan.notes or []
            loan.notes.append({
                "date": datetime.now().date(),
                "author": denied_by,
                "content": denial_notes,
                "type": "denial"
            })
        
        # Update in repository
        updated_loan = self.loan_repository.update(loan)
        
        # Send notification
        self.notification_service.send_notification(
            recipient_id=loan.customer_id,
            subject="Loan Application Update",
            message=(
                f"We regret to inform you that your application for a {loan.loan_type.value} loan "
                f"of {loan.amount} has been denied. "
                f"Reason: {denial_reason}"
            )
        )
        
        return updated_loan
