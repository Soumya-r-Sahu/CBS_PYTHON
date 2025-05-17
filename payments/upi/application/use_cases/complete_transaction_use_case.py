"""
Complete Transaction use case for UPI payments.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from uuid import UUID

from ...domain.entities.upi_transaction import UpiTransaction, UpiTransactionStatus
from ..interfaces.upi_transaction_repository_interface import UpiTransactionRepositoryInterface
from ..interfaces.notification_service_interface import UpiNotificationServiceInterface


@dataclass
class CompleteTransactionRequest:
    """Data Transfer Object for complete transaction request."""
    transaction_id: UUID
    reference_id: str


@dataclass
class CompleteTransactionResponse:
    """Data Transfer Object for complete transaction response."""
    success: bool = False
    message: Optional[str] = None
    error_code: Optional[str] = None


class CompleteTransactionUseCase:
    """Use case for completing a UPI transaction."""
    
    def __init__(
        self,
        transaction_repository: UpiTransactionRepositoryInterface,
        notification_service: UpiNotificationServiceInterface
    ):
        """
        Initialize the use case with required dependencies.
        
        Args:
            transaction_repository: Repository for UPI transactions
            notification_service: Service for sending notifications
        """
        self.transaction_repository = transaction_repository
        self.notification_service = notification_service
    
    def execute(self, request: CompleteTransactionRequest) -> CompleteTransactionResponse:
        """
        Execute the complete transaction use case.
        
        Args:
            request: DTO containing complete transaction request data
            
        Returns:
            DTO containing the result of the operation
        """
        # Fetch the transaction
        transaction = self.transaction_repository.get_by_id(request.transaction_id)
        if not transaction:
            return CompleteTransactionResponse(
                success=False,
                message="Transaction not found",
                error_code="TRANSACTION_NOT_FOUND"
            )
        
        # Check if transaction can be completed
        if transaction.status not in [UpiTransactionStatus.INITIATED, UpiTransactionStatus.PENDING]:
            return CompleteTransactionResponse(
                success=False,
                message=f"Transaction cannot be completed from status: {transaction.status.value}",
                error_code="INVALID_TRANSACTION_STATUS"
            )
        
        try:
            # Update transaction status
            transaction.complete(request.reference_id)
            
            # Save updated transaction
            self.transaction_repository.update(transaction)
            
            # Send notifications
            try:
                self.notification_service.send_transaction_completed_notification(transaction)
            except Exception:
                # Continue even if notification fails
                pass
            
            return CompleteTransactionResponse(
                success=True,
                message="Transaction completed successfully"
            )
        except Exception as e:
            return CompleteTransactionResponse(
                success=False,
                message=f"Failed to complete transaction: {str(e)}",
                error_code="TRANSACTION_UPDATE_ERROR"
            )
