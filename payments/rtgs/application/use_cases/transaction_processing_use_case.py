"""
RTGS Transaction Processing Use Case.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from ...domain.entities.rtgs_transaction import RTGSTransaction, RTGSStatus
from ..interfaces.rtgs_transaction_repository_interface import RTGSTransactionRepositoryInterface
from ..interfaces.rtgs_rbi_interface_service_interface import RTGSRBIInterfaceServiceInterface
from ..interfaces.rtgs_audit_log_service_interface import RTGSAuditLogServiceInterface
from ..interfaces.rtgs_notification_service_interface import RTGSNotificationServiceInterface


class RTGSTransactionProcessingUseCase:
    """Use case for processing RTGS transactions."""
    
    def __init__(
        self,
        transaction_repository: RTGSTransactionRepositoryInterface,
        rbi_interface_service: RTGSRBIInterfaceServiceInterface,
        audit_log_service: RTGSAuditLogServiceInterface,
        notification_service: RTGSNotificationServiceInterface
    ):
        """
        Initialize the use case.
        
        Args:
            transaction_repository: Repository for transaction persistence
            rbi_interface_service: Service for RBI RTGS interface
            audit_log_service: Service for audit logging
            notification_service: Service for notifications
        """
        self.transaction_repository = transaction_repository
        self.rbi_interface_service = rbi_interface_service
        self.audit_log_service = audit_log_service
        self.notification_service = notification_service
    
    def execute(
        self,
        transaction_id: UUID,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an RTGS transaction by sending it to the RBI RTGS system.
        
        Args:
            transaction_id: The transaction ID
            user_id: Optional user ID for audit logging
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            # Get transaction from repository
            transaction = self.transaction_repository.get_by_id(transaction_id)
            if not transaction:
                return {
                    "status": "error",
                    "error_type": "not_found",
                    "message": f"Transaction with ID {transaction_id} not found"
                }
            
            # Check if transaction is in a valid state for processing
            if transaction.status != RTGSStatus.INITIATED and transaction.status != RTGSStatus.VALIDATED:
                return {
                    "status": "error",
                    "error_type": "invalid_state",
                    "message": f"Transaction is in {transaction.status.value} state and cannot be processed"
                }
            
            # Update status to PROCESSING
            old_status = transaction.status
            transaction.status = RTGSStatus.PROCESSING
            transaction.updated_at = datetime.utcnow()
            
            # Save the updated transaction
            transaction = self.transaction_repository.update(transaction)
            
            # Log status change
            self.audit_log_service.log_transaction_status_changed(
                transaction, 
                old_status.value, 
                RTGSStatus.PROCESSING.value, 
                user_id
            )
            
            # Send to RBI RTGS system
            rbi_response = self.rbi_interface_service.send_transaction(transaction)
            
            # Update transaction with RBI response
            if rbi_response.get("status") == "success":
                old_status = transaction.status
                transaction.status = RTGSStatus.PENDING_RBI
                transaction.utr_number = rbi_response.get("utr_number")
                transaction.processed_at = datetime.utcnow()
                transaction.updated_at = datetime.utcnow()
                
                # Save the updated transaction
                transaction = self.transaction_repository.update(transaction)
                
                # Log status change
                self.audit_log_service.log_transaction_status_changed(
                    transaction, 
                    old_status.value, 
                    RTGSStatus.PENDING_RBI.value, 
                    user_id
                )
                
                return {
                    "status": "success",
                    "transaction_id": str(transaction.id),
                    "transaction_status": transaction.status.value,
                    "utr_number": transaction.utr_number,
                    "processed_at": transaction.processed_at.isoformat()
                }
            else:
                # Update transaction as FAILED
                old_status = transaction.status
                transaction.status = RTGSStatus.FAILED
                transaction.updated_at = datetime.utcnow()
                
                # Save the updated transaction
                transaction = self.transaction_repository.update(transaction)
                
                # Log status change
                self.audit_log_service.log_transaction_status_changed(
                    transaction, 
                    old_status.value, 
                    RTGSStatus.FAILED.value, 
                    user_id
                )
                
                # Send failure notification
                self.notification_service.notify_transaction_failed(
                    transaction, 
                    rbi_response.get("message", "Failed to process transaction")
                )
                
                return {
                    "status": "error",
                    "error_type": "rbi_error",
                    "message": rbi_response.get("message", "Failed to process transaction"),
                    "transaction_id": str(transaction.id),
                    "transaction_status": transaction.status.value
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
