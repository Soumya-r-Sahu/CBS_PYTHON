"""
RTGS Batch Processing Use Case.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from ...domain.entities.rtgs_batch import RTGSBatch, RTGSBatchStatus
from ...domain.entities.rtgs_transaction import RTGSTransaction, RTGSStatus
from ...domain.services.rtgs_batch_service import RTGSBatchService
from ..interfaces.rtgs_batch_repository_interface import RTGSBatchRepositoryInterface
from ..interfaces.rtgs_transaction_repository_interface import RTGSTransactionRepositoryInterface
from ..interfaces.rtgs_rbi_interface_service_interface import RTGSRBIInterfaceServiceInterface
from ..interfaces.rtgs_audit_log_service_interface import RTGSAuditLogServiceInterface


class RTGSBatchProcessingUseCase:
    """Use case for processing RTGS transaction batches."""
    
    def __init__(
        self,
        batch_repository: RTGSBatchRepositoryInterface,
        transaction_repository: RTGSTransactionRepositoryInterface,
        batch_service: RTGSBatchService,
        rbi_interface_service: RTGSRBIInterfaceServiceInterface,
        audit_log_service: RTGSAuditLogServiceInterface
    ):
        """
        Initialize the use case.
        
        Args:
            batch_repository: Repository for batch persistence
            transaction_repository: Repository for transaction persistence
            batch_service: Service for batch operations
            rbi_interface_service: Service for RBI RTGS interface
            audit_log_service: Service for audit logging
        """
        self.batch_repository = batch_repository
        self.transaction_repository = transaction_repository
        self.batch_service = batch_service
        self.rbi_interface_service = rbi_interface_service
        self.audit_log_service = audit_log_service
    
    def create_batch(self, scheduled_time: datetime = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new batch for processing.
        
        Args:
            scheduled_time: Time when the batch is scheduled to be processed
            user_id: Optional user ID for audit logging
            
        Returns:
            Dict[str, Any]: Batch creation result
        """
        try:
            if not scheduled_time:
                # Use the batch service to calculate next settlement time
                scheduled_time = self.batch_service.calculate_expected_settlement_time()
            
            # Generate batch number
            batch_number = self.batch_service.generate_batch_number(scheduled_time)
            
            # Create batch entity
            batch = RTGSBatch.create(
                batch_number=batch_number,
                scheduled_time=scheduled_time
            )
            
            # Save to repository
            saved_batch = self.batch_repository.save(batch)
            
            # Log the batch creation
            self.audit_log_service.log_batch_created(saved_batch, user_id)
            
            return {
                "status": "success",
                "batch_id": str(saved_batch.id),
                "batch_number": saved_batch.batch_number,
                "scheduled_time": saved_batch.scheduled_time.isoformat(),
                "status": saved_batch.status.value
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def add_transaction_to_batch(
        self,
        batch_id: UUID,
        transaction_id: UUID,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a transaction to a batch.
        
        Args:
            batch_id: The batch ID
            transaction_id: The transaction ID
            user_id: Optional user ID for audit logging
            
        Returns:
            Dict[str, Any]: Operation result
        """
        try:
            # Get batch and transaction
            batch = self.batch_repository.get_by_id(batch_id)
            if not batch:
                return {
                    "status": "error",
                    "error_type": "not_found",
                    "message": f"Batch with ID {batch_id} not found"
                }
            
            transaction = self.transaction_repository.get_by_id(transaction_id)
            if not transaction:
                return {
                    "status": "error",
                    "error_type": "not_found",
                    "message": f"Transaction with ID {transaction_id} not found"
                }
            
            # Check if batch is in a valid state
            if batch.status != RTGSBatchStatus.CREATED:
                return {
                    "status": "error",
                    "error_type": "invalid_state",
                    "message": f"Batch is in {batch.status.value} state and cannot be modified"
                }
            
            # Check if transaction is in a valid state
            if transaction.status != RTGSStatus.VALIDATED and transaction.status != RTGSStatus.INITIATED:
                return {
                    "status": "error",
                    "error_type": "invalid_state",
                    "message": f"Transaction is in {transaction.status.value} state and cannot be added to batch"
                }
            
            # Add transaction to batch
            batch.add_transaction(transaction.id, transaction.payment_details.amount)
            
            # Update the transaction
            transaction.status = RTGSStatus.PROCESSING
            transaction.updated_at = datetime.utcnow()
            
            # Save updates
            updated_batch = self.batch_repository.update(batch)
            updated_transaction = self.transaction_repository.update(transaction)
            
            # Log the updates
            self.audit_log_service.log_batch_updated(updated_batch, user_id)
            self.audit_log_service.log_transaction_status_changed(
                updated_transaction,
                RTGSStatus.VALIDATED.value,
                RTGSStatus.PROCESSING.value,
                user_id
            )
            
            return {
                "status": "success",
                "batch_id": str(updated_batch.id),
                "transaction_id": str(updated_transaction.id),
                "message": "Transaction successfully added to batch"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def process_batch(self, batch_id: UUID, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a batch by sending it to the RBI RTGS system.
        
        Args:
            batch_id: The batch ID
            user_id: Optional user ID for audit logging
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            # Get batch
            batch = self.batch_repository.get_by_id(batch_id)
            if not batch:
                return {
                    "status": "error",
                    "error_type": "not_found",
                    "message": f"Batch with ID {batch_id} not found"
                }
            
            # Check if batch is in a valid state
            if batch.status != RTGSBatchStatus.CREATED:
                return {
                    "status": "error",
                    "error_type": "invalid_state",
                    "message": f"Batch is in {batch.status.value} state and cannot be processed"
                }
            
            # Check if there are transactions in the batch
            if batch.transaction_count == 0:
                return {
                    "status": "error",
                    "error_type": "empty_batch",
                    "message": "Batch has no transactions to process"
                }
            
            # Fetch all transactions in the batch
            transactions = []
            for tx_id in batch.transaction_ids:
                tx = self.transaction_repository.get_by_id(tx_id)
                if tx:
                    transactions.append(tx)
            
            # Update batch status
            old_status = batch.status
            batch.status = RTGSBatchStatus.PROCESSING
            batch.processed_at = datetime.utcnow()
            batch.updated_at = datetime.utcnow()
            
            # Save updated batch
            updated_batch = self.batch_repository.update(batch)
            
            # Log status change
            self.audit_log_service.log_batch_status_changed(
                updated_batch,
                old_status.value,
                RTGSBatchStatus.PROCESSING.value,
                user_id
            )
            
            # Send to RBI RTGS system
            rbi_response = self.rbi_interface_service.send_batch(updated_batch, transactions)
            
            if rbi_response.get("status") == "success":
                # Update batch status
                old_status = updated_batch.status
                updated_batch.status = RTGSBatchStatus.SENT_TO_RBI
                updated_batch.updated_at = datetime.utcnow()
                
                # Save updated batch
                final_batch = self.batch_repository.update(updated_batch)
                
                # Log status change
                self.audit_log_service.log_batch_status_changed(
                    final_batch,
                    old_status.value,
                    RTGSBatchStatus.SENT_TO_RBI.value,
                    user_id
                )
                
                # Update transaction statuses
                for tx in transactions:
                    tx.status = RTGSStatus.PENDING_RBI
                    tx.utr_number = rbi_response.get("details", {}).get("utr_numbers", {}).get(str(tx.id))
                    tx.updated_at = datetime.utcnow()
                    self.transaction_repository.update(tx)
                
                return {
                    "status": "success",
                    "batch_id": str(final_batch.id),
                    "batch_number": final_batch.batch_number,
                    "transaction_count": final_batch.transaction_count,
                    "total_amount": final_batch.total_amount,
                    "message": "Batch successfully sent to RBI RTGS system"
                }
            else:
                # Update batch status to failed
                old_status = updated_batch.status
                updated_batch.status = RTGSBatchStatus.FAILED
                updated_batch.updated_at = datetime.utcnow()
                
                # Save updated batch
                failed_batch = self.batch_repository.update(updated_batch)
                
                # Log status change
                self.audit_log_service.log_batch_status_changed(
                    failed_batch,
                    old_status.value,
                    RTGSBatchStatus.FAILED.value,
                    user_id
                )
                
                return {
                    "status": "error",
                    "error_type": "rbi_error",
                    "message": rbi_response.get("message", "Failed to process batch"),
                    "batch_id": str(failed_batch.id)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
