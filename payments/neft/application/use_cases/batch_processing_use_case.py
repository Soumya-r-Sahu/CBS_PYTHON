"""
NEFT Batch Processing Use Case.
"""
from typing import Dict, Any, Optional, List
from uuid import UUID

from ...domain.entities.neft_batch import NEFTBatch, NEFTBatchStatus
from ...domain.entities.neft_transaction import NEFTTransaction, NEFTStatus
from ..interfaces.neft_batch_repository_interface import NEFTBatchRepositoryInterface
from ..interfaces.neft_transaction_repository_interface import NEFTTransactionRepositoryInterface
from ..interfaces.neft_rbi_interface_service_interface import NEFTRbiInterfaceServiceInterface
from ..interfaces.neft_audit_log_service_interface import NEFTAuditLogServiceInterface
from ..interfaces.neft_notification_service_interface import NEFTNotificationServiceInterface


class NEFTBatchProcessingUseCase:
    """Use case for processing NEFT batches."""
    
    def __init__(
        self,
        batch_repository: NEFTBatchRepositoryInterface,
        transaction_repository: NEFTTransactionRepositoryInterface,
        rbi_interface_service: NEFTRbiInterfaceServiceInterface,
        audit_log_service: NEFTAuditLogServiceInterface,
        notification_service: NEFTNotificationServiceInterface,
        mock_mode: bool = False
    ):
        """
        Initialize the use case.
        
        Args:
            batch_repository: Repository for batch persistence
            transaction_repository: Repository for transaction persistence
            rbi_interface_service: Service for RBI interface
            audit_log_service: Service for audit logging
            notification_service: Service for notifications
            mock_mode: Whether to run in mock mode
        """
        self.batch_repository = batch_repository
        self.transaction_repository = transaction_repository
        self.rbi_interface_service = rbi_interface_service
        self.audit_log_service = audit_log_service
        self.notification_service = notification_service
        self.mock_mode = mock_mode
    
    def process_batch(
        self,
        batch_id: UUID,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a NEFT batch.
        
        Args:
            batch_id: Batch ID to process
            user_id: Optional user ID for audit logging
            
        Returns:
            Dict[str, Any]: Response with batch details or error
        """
        try:
            # Get batch
            batch = self.batch_repository.get_by_id(batch_id)
            if not batch:
                return {
                    "status": "error",
                    "error_type": "not_found",
                    "message": f"Batch not found: {batch_id}"
                }
            
            # Check if batch is in valid state
            if batch.status != NEFTBatchStatus.PENDING:
                return {
                    "status": "error",
                    "error_type": "invalid_state",
                    "message": f"Batch {batch_id} is in {batch.status} state, cannot be processed"
                }
            
            # Update batch status
            previous_status = batch.status
            batch.update_status(NEFTBatchStatus.PROCESSING)
            self.batch_repository.update(batch)
            
            # Log the update
            self.audit_log_service.log_batch_updated(batch, previous_status.value, user_id)
            
            # Get all transactions in the batch
            transactions = []
            for tx_id in batch.transaction_ids:
                tx = self.transaction_repository.get_by_id(tx_id)
                if tx:
                    transactions.append(tx)
            
            # Process transactions
            updated_batch, updated_transactions = self._process_batch_transactions(batch, transactions)
            
            # Send notification
            self.notification_service.notify_batch_completed(
                updated_batch.batch_number,
                updated_batch.completed_transactions,
                updated_batch.failed_transactions
            )
            
            # Return response
            return {
                "status": "success",
                "batch_id": str(updated_batch.id),
                "batch_number": updated_batch.batch_number,
                "batch_status": updated_batch.status.value,
                "total_transactions": updated_batch.total_transactions,
                "successful_transactions": updated_batch.completed_transactions,
                "failed_transactions": updated_batch.failed_transactions,
                "total_amount": updated_batch.total_amount,
                "completed_at": updated_batch.completed_at.isoformat() if updated_batch.completed_at else None,
                "message": f"NEFT batch processed: {updated_batch.completed_transactions}/{updated_batch.total_transactions} successful"
            }
            
        except Exception as e:
            # Log the error
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def _process_batch_transactions(
        self,
        batch: NEFTBatch,
        transactions: List[NEFTTransaction]
    ) -> tuple[NEFTBatch, List[NEFTTransaction]]:
        """
        Process all transactions in a batch.
        
        Args:
            batch: The batch to process
            transactions: The transactions in the batch
            
        Returns:
            tuple[NEFTBatch, List[NEFTTransaction]]: Updated batch and transactions
        """
        # In mock mode or real mode, process through the RBI interface
        updated_batch, updated_transactions = self.rbi_interface_service.submit_batch(batch, transactions)
        
        # Save all updated transactions
        for tx in updated_transactions:
            self.transaction_repository.update(tx)
            
            # Send notifications for each transaction
            if tx.status == NEFTStatus.COMPLETED:
                self.notification_service.notify_transaction_completed(tx)
            elif tx.status in [NEFTStatus.FAILED, NEFTStatus.RETURNED]:
                self.notification_service.notify_transaction_failed(tx)
        
        # Save updated batch
        return self.batch_repository.update(updated_batch), updated_transactions
