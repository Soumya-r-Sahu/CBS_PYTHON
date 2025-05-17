"""
NEFT Transaction Processing Use Case.
"""
from typing import Dict, Any, Optional
from uuid import UUID

from ...domain.entities.neft_transaction import NEFTTransaction, NEFTStatus
from ...domain.services.neft_batch_service import NEFTBatchService
from ...domain.entities.neft_batch import NEFTBatch, NEFTBatchStatus
from ..interfaces.neft_transaction_repository_interface import NEFTTransactionRepositoryInterface
from ..interfaces.neft_batch_repository_interface import NEFTBatchRepositoryInterface
from ..interfaces.neft_audit_log_service_interface import NEFTAuditLogServiceInterface
from ..interfaces.neft_notification_service_interface import NEFTNotificationServiceInterface


class NEFTTransactionProcessingUseCase:
    """Use case for processing NEFT transactions."""
    
    def __init__(
        self,
        transaction_repository: NEFTTransactionRepositoryInterface,
        batch_repository: NEFTBatchRepositoryInterface,
        batch_service: NEFTBatchService,
        audit_log_service: NEFTAuditLogServiceInterface,
        notification_service: NEFTNotificationServiceInterface
    ):
        """
        Initialize the use case.
        
        Args:
            transaction_repository: Repository for transaction persistence
            batch_repository: Repository for batch persistence
            batch_service: Service for batch operations
            audit_log_service: Service for audit logging
            notification_service: Service for notifications
        """
        self.transaction_repository = transaction_repository
        self.batch_repository = batch_repository
        self.batch_service = batch_service
        self.audit_log_service = audit_log_service
        self.notification_service = notification_service
    
    def process_transaction(
        self,
        transaction_id: UUID,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a NEFT transaction (validate and queue for processing).
        
        Args:
            transaction_id: Transaction ID to process
            user_id: Optional user ID for audit logging
            
        Returns:
            Dict[str, Any]: Response with transaction details or error
        """
        try:
            # Get transaction
            transaction = self.transaction_repository.get_by_id(transaction_id)
            if not transaction:
                return {
                    "status": "error",
                    "error_type": "not_found",
                    "message": f"Transaction not found: {transaction_id}"
                }
            
            # Check if transaction is in valid state
            if transaction.status != NEFTStatus.INITIATED:
                return {
                    "status": "error",
                    "error_type": "invalid_state",
                    "message": f"Transaction {transaction_id} is in {transaction.status} state, cannot be processed"
                }
            
            # Update status to VALIDATED
            previous_status = transaction.status
            transaction.update_status(NEFTStatus.VALIDATED)
            
            # Save transaction
            updated_transaction = self.transaction_repository.update(transaction)
            
            # Log the update
            self.audit_log_service.log_transaction_updated(
                updated_transaction, 
                previous_status.value,
                user_id
            )
            
            # Add to batch
            added_transaction = self._add_to_batch(updated_transaction)
            
            # Return response
            return {
                "status": "success",
                "transaction_id": str(added_transaction.id),
                "transaction_status": added_transaction.status.value,
                "transaction_reference": added_transaction.transaction_reference,
                "batch_number": added_transaction.batch_number,
                "message": "NEFT transaction processed successfully"
            }
            
        except Exception as e:
            # Log the error
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def _add_to_batch(self, transaction: NEFTTransaction) -> NEFTTransaction:
        """
        Add a transaction to the next available NEFT batch.
        
        Args:
            transaction: Transaction to add to batch
            
        Returns:
            NEFTTransaction: Updated transaction
        """
        # Calculate next batch time
        next_batch_time = self.batch_service.calculate_next_batch_time()
        
        # Generate batch number
        batch_number = self.batch_service.generate_batch_number(next_batch_time)
        
        # Get or create batch
        batch = self.batch_repository.get_by_batch_number(batch_number)
        if not batch:
            batch = NEFTBatch.create(batch_number, next_batch_time)
        
        # Add transaction to batch
        batch.add_transaction(transaction.id, transaction.payment_details.amount)
        
        # Save batch
        self.batch_repository.save(batch)
        
        # Update transaction with batch information
        previous_status = transaction.status
        transaction.add_to_batch(batch_number)
        
        # Save updated transaction
        updated_transaction = self.transaction_repository.update(transaction)
        
        # Log the update
        self.audit_log_service.log_transaction_updated(
            updated_transaction,
            previous_status.value
        )
        
        return updated_transaction
