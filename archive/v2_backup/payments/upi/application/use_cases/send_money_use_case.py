"""
Send Money use case for UPI payments.
"""
from dataclasses import dataclass
from datetime import date
from typing import Dict, Any, Optional
from uuid import UUID

from ...domain.entities.upi_transaction import UpiTransaction
from ...domain.services.transaction_rules_service import UpiTransactionRulesService
from ...domain.services.vpa_validation_service import VpaValidationService
from ..interfaces.upi_transaction_repository_interface import UpiTransactionRepositoryInterface
from ..interfaces.notification_service_interface import UpiNotificationServiceInterface


@dataclass
class SendMoneyRequest:
    """Data Transfer Object for send money request."""
    sender_vpa: str
    receiver_vpa: str
    amount: float
    remarks: Optional[str] = None


@dataclass
class SendMoneyResponse:
    """Data Transfer Object for send money response."""
    transaction_id: Optional[UUID] = None
    success: bool = False
    message: Optional[str] = None
    error_code: Optional[str] = None


class SendMoneyUseCase:
    """Use case for sending money via UPI."""
    
    def __init__(
        self,
        transaction_repository: UpiTransactionRepositoryInterface,
        notification_service: UpiNotificationServiceInterface,
        transaction_rules_service: UpiTransactionRulesService,
        vpa_validation_service: VpaValidationService
    ):
        """
        Initialize the use case with required dependencies.
        
        Args:
            transaction_repository: Repository for UPI transactions
            notification_service: Service for sending notifications
            transaction_rules_service: Service for validating transaction rules
            vpa_validation_service: Service for validating VPAs
        """
        self.transaction_repository = transaction_repository
        self.notification_service = notification_service
        self.transaction_rules_service = transaction_rules_service
        self.vpa_validation_service = vpa_validation_service
    
    def execute(self, request: SendMoneyRequest) -> SendMoneyResponse:
        """
        Execute the send money use case.
        
        Args:
            request: DTO containing send money request data
            
        Returns:
            DTO containing the result of the operation
        """
        # Validate sender VPA
        sender_vpa_validation = self.vpa_validation_service.validate_vpa(request.sender_vpa)
        if not sender_vpa_validation['is_valid']:
            return SendMoneyResponse(
                success=False,
                message=f"Invalid sender VPA: {sender_vpa_validation['message']}",
                error_code="INVALID_SENDER_VPA"
            )
        
        # Validate receiver VPA
        receiver_vpa_validation = self.vpa_validation_service.validate_vpa(request.receiver_vpa)
        if not receiver_vpa_validation['is_valid']:
            return SendMoneyResponse(
                success=False,
                message=f"Invalid receiver VPA: {receiver_vpa_validation['message']}",
                error_code="INVALID_RECEIVER_VPA"
            )
        
        # Get daily total for sender
        today = date.today()
        daily_total = self.transaction_repository.get_daily_transaction_total(
            request.sender_vpa, today
        )
        
        # Create a new transaction entity
        try:
            transaction = UpiTransaction.create(
                sender_vpa=request.sender_vpa,
                receiver_vpa=request.receiver_vpa,
                amount=request.amount,
                remarks=request.remarks
            )
        except ValueError as e:
            return SendMoneyResponse(
                success=False,
                message=str(e),
                error_code="INVALID_TRANSACTION_DATA"
            )
        
        # Validate transaction rules
        validation_result = self.transaction_rules_service.validate_transaction(
            transaction, daily_total
        )
        if not validation_result['is_valid']:
            return SendMoneyResponse(
                success=False,
                message=validation_result['message'],
                error_code="TRANSACTION_RULE_VIOLATION"
            )
        
        # Save the transaction
        try:
            self.transaction_repository.save(transaction)
        except Exception as e:
            return SendMoneyResponse(
                success=False,
                message=f"Failed to save transaction: {str(e)}",
                error_code="REPOSITORY_ERROR"
            )
        
        # Send notification
        try:
            self.notification_service.send_transaction_initiated_notification(
                transaction, transaction.sender_vpa
            )
        except Exception:
            # Continue even if notification fails
            pass
        
        return SendMoneyResponse(
            transaction_id=transaction.transaction_id,
            success=True,
            message="Transaction initiated successfully"
        )
