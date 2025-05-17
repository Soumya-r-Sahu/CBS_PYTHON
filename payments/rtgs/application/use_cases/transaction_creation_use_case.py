"""
RTGS Transaction Creation Use Case.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from ...domain.entities.rtgs_transaction import RTGSTransaction, RTGSPaymentDetails, RTGSStatus
from ...domain.services.rtgs_validation_service import RTGSValidationService
from ..interfaces.rtgs_transaction_repository_interface import RTGSTransactionRepositoryInterface
from ..interfaces.rtgs_audit_log_service_interface import RTGSAuditLogServiceInterface
from ..interfaces.rtgs_notification_service_interface import RTGSNotificationServiceInterface


class RTGSTransactionCreationUseCase:
    """Use case for creating RTGS transactions."""
    
    def __init__(
        self,
        transaction_repository: RTGSTransactionRepositoryInterface,
        validation_service: RTGSValidationService,
        audit_log_service: RTGSAuditLogServiceInterface,
        notification_service: RTGSNotificationServiceInterface
    ):
        """
        Initialize the use case.
        
        Args:
            transaction_repository: Repository for transaction persistence
            validation_service: Service for transaction validation
            audit_log_service: Service for audit logging
            notification_service: Service for notifications
        """
        self.transaction_repository = transaction_repository
        self.validation_service = validation_service
        self.audit_log_service = audit_log_service
        self.notification_service = notification_service
    
    def execute(
        self,
        payment_data: Dict[str, Any],
        customer_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new RTGS transaction.
        
        Args:
            payment_data: Payment details
            customer_id: Optional customer ID for tracking
            user_id: Optional user ID for audit logging
            
        Returns:
            Dict[str, Any]: Response with transaction details or error
        """
        try:
            # Extract payment details
            payment_details = RTGSPaymentDetails(
                sender_account_number=payment_data.get("sender_account_number", ""),
                sender_ifsc_code=payment_data.get("sender_ifsc_code", ""),
                sender_account_type=payment_data.get("sender_account_type", "SAVINGS"),
                sender_name=payment_data.get("sender_name", ""),
                beneficiary_account_number=payment_data.get("beneficiary_account_number", ""),
                beneficiary_ifsc_code=payment_data.get("beneficiary_ifsc_code", ""),
                beneficiary_account_type=payment_data.get("beneficiary_account_type", "SAVINGS"),
                beneficiary_name=payment_data.get("beneficiary_name", ""),
                amount=float(payment_data.get("amount", 0)),
                payment_reference=payment_data.get("reference", ""),
                remarks=payment_data.get("remarks", "")
            )
            
            # Validate payment details
            validation_error = self.validation_service.validate_payment_details(payment_details)
            if validation_error:
                return {
                    "status": "error",
                    "error_type": "validation",
                    "message": validation_error
                }
            
            # Create transaction
            transaction = RTGSTransaction(
                payment_details=payment_details
            )
            
            # Generate transaction reference
            transaction.transaction_reference = f"RTGS{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4().hex)[:8].upper()}"
            
            # Save to repository
            saved_transaction = self.transaction_repository.save(transaction)
            
            # Log the transaction creation
            self.audit_log_service.log_transaction_created(saved_transaction, user_id)
            
            # Send notification
            self.notification_service.notify_transaction_initiated(saved_transaction)
            
            # Return response
            return {
                "status": "success",
                "transaction_id": str(saved_transaction.id),
                "amount": payment_details.amount,
                "beneficiary_account": payment_details.beneficiary_account_number,
                "beneficiary_ifsc": payment_details.beneficiary_ifsc_code,
                "transaction_status": saved_transaction.status.value,
                "transaction_reference": saved_transaction.transaction_reference,
                "created_at": saved_transaction.created_at.isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
