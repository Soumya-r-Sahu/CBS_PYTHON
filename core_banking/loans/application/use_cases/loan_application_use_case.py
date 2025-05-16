"""
Loan Application Use Case

This module implements the business logic for processing a loan application.
"""
from datetime import datetime
import uuid
from decimal import Decimal
from typing import Optional, Dict, Any

from ...domain.entities.loan import Loan, LoanStatus, LoanType, LoanTerms, RepaymentFrequency
from ..interfaces.loan_repository_interface import LoanRepositoryInterface
from ..interfaces.notification_service_interface import NotificationServiceInterface
from ..interfaces.document_storage_interface import DocumentStorageInterface


class LoanApplicationError(Exception):
    """Exception raised for errors in the loan application process."""
    pass


class LoanApplicationUseCase:
    """
    Handles the business logic for submitting a loan application.
    
    This use case implements the process of submitting a new loan application,
    including validation, creation of the loan entity, and notifications.
    """
    
    def __init__(
        self,
        loan_repository: LoanRepositoryInterface,
        notification_service: NotificationServiceInterface,
        document_storage: DocumentStorageInterface
    ):
        """
        Initialize the use case with required dependencies.
        
        Args:
            loan_repository: Repository for loan data persistence
            notification_service: Service for sending notifications
            document_storage: Service for storing loan documents
        """
        self.loan_repository = loan_repository
        self.notification_service = notification_service
        self.document_storage = document_storage
    
    def execute(
        self,
        customer_id: str,
        loan_type: LoanType,
        amount: Decimal,
        term_months: int,
        interest_rate: Decimal,
        repayment_frequency: RepaymentFrequency,
        purpose: str,
        documents: Dict[str, bytes] = None,
        collateral_description: Optional[str] = None,
        collateral_value: Optional[Decimal] = None,
        cosigner_id: Optional[str] = None,
        grace_period_days: int = 0,
    ) -> Loan:
        """
        Process a loan application.
        
        Args:
            customer_id: ID of the customer applying for the loan
            loan_type: Type of loan
            amount: Requested loan amount
            term_months: Loan term in months
            interest_rate: Annual interest rate
            repayment_frequency: Frequency of repayments
            purpose: Purpose of the loan
            documents: Dictionary of document name to document content
            collateral_description: Description of collateral (if applicable)
            collateral_value: Value of collateral (if applicable)
            cosigner_id: ID of cosigner (if applicable)
            grace_period_days: Grace period in days
            
        Returns:
            The created loan entity
            
        Raises:
            LoanApplicationError: If validation fails or application cannot be processed
        """
        # Basic validation
        self._validate_loan_application(
            customer_id=customer_id,
            loan_type=loan_type,
            amount=amount,
            term_months=term_months,
            interest_rate=interest_rate
        )
        
        # Store documents if provided
        document_references = {}
        if documents:
            for doc_name, doc_content in documents.items():
                doc_ref = self.document_storage.store_document(
                    customer_id=customer_id,
                    document_type=doc_name,
                    content=doc_content
                )
                document_references[doc_name] = doc_ref
        
        # Create loan terms
        loan_terms = LoanTerms(
            interest_rate=interest_rate,
            term_months=term_months,
            repayment_frequency=repayment_frequency,
            grace_period_days=grace_period_days
        )
        
        # Create the loan entity
        loan = Loan(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            loan_type=loan_type,
            amount=amount,
            terms=loan_terms,
            status=LoanStatus.PENDING,
            purpose=purpose,
            application_date=datetime.now().date(),
            document_references=document_references,
            collateral_description=collateral_description,
            collateral_value=collateral_value,
            cosigner_id=cosigner_id
        )
        
        # Save to repository
        created_loan = self.loan_repository.create(loan)
        
        # Send notification
        self.notification_service.send_notification(
            recipient_id=customer_id,
            subject="Loan Application Received",
            message=(
                f"Your application for a {loan_type.value} loan "
                f"of {amount} has been received and is under review. "
                f"Reference number: {created_loan.id}"
            )
        )
        
        return created_loan
    
    def _validate_loan_application(
        self,
        customer_id: str,
        loan_type: LoanType,
        amount: Decimal,
        term_months: int,
        interest_rate: Decimal
    ) -> None:
        """
        Validate loan application inputs.
        
        Args:
            customer_id: ID of the customer
            loan_type: Type of loan
            amount: Requested loan amount
            term_months: Loan term in months
            interest_rate: Annual interest rate
            
        Raises:
            LoanApplicationError: If validation fails
        """
        if not customer_id:
            raise LoanApplicationError("Customer ID is required")
        
        if not loan_type:
            raise LoanApplicationError("Loan type is required")
        
        if amount <= Decimal("0"):
            raise LoanApplicationError("Loan amount must be positive")
        
        if term_months <= 0:
            raise LoanApplicationError("Loan term must be positive")
        
        if interest_rate < Decimal("0"):
            raise LoanApplicationError("Interest rate cannot be negative")
        
        # Additional validation logic could be added here
        # For example, checking customer credit score or loan limits
