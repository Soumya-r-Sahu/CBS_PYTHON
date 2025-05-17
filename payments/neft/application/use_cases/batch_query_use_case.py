"""
NEFT Batch Query Use Case.
"""
from typing import Dict, Any, Optional, List
from uuid import UUID

from ...domain.entities.neft_batch import NEFTBatch, NEFTBatchStatus
from ..interfaces.neft_batch_repository_interface import NEFTBatchRepositoryInterface
from ..interfaces.neft_audit_log_service_interface import NEFTAuditLogServiceInterface


class NEFTBatchQueryUseCase:
    """Use case for querying NEFT batches."""
    
    def __init__(
        self,
        batch_repository: NEFTBatchRepositoryInterface,
        audit_log_service: NEFTAuditLogServiceInterface
    ):
        """
        Initialize the use case.
        
        Args:
            batch_repository: Repository for batch persistence
            audit_log_service: Service for audit logging
        """
        self.batch_repository = batch_repository
        self.audit_log_service = audit_log_service
    
    def get_batch(
        self,
        batch_id: UUID,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get details of a NEFT batch.
        
        Args:
            batch_id: Batch ID to query
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
                    "message": f"Batch {batch_id} not found"
                }
            
            # Prepare response
            response = {
                "status": "success",
                "batch_id": str(batch.id),
                "batch_number": batch.batch_number,
                "batch_status": batch.status.value,
                "batch_time": batch.batch_time.isoformat(),
                "total_transactions": batch.total_transactions,
                "total_amount": batch.total_amount,
                "completed_transactions": batch.completed_transactions,
                "failed_transactions": batch.failed_transactions,
                "created_at": batch.created_at.isoformat(),
                "updated_at": batch.updated_at.isoformat()
            }
            
            # Add additional info based on status
            if batch.status in [NEFTBatchStatus.SUBMITTED, NEFTBatchStatus.COMPLETED, NEFTBatchStatus.PARTIALLY_COMPLETED]:
                if batch.submitted_at:
                    response["submitted_at"] = batch.submitted_at.isoformat()
            
            if batch.status in [NEFTBatchStatus.COMPLETED, NEFTBatchStatus.FAILED, NEFTBatchStatus.PARTIALLY_COMPLETED]:
                if batch.completed_at:
                    response["completed_at"] = batch.completed_at.isoformat()
            
            return response
            
        except Exception as e:
            # Log the error
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def get_batches_by_date(
        self,
        date_str: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get batches for a specific date.
        
        Args:
            date_str: Date string in format YYYY-MM-DD
            user_id: Optional user ID for audit logging
            
        Returns:
            Dict[str, Any]: Response with batch list or error
        """
        try:
            # Get batches
            batches = self.batch_repository.get_batches_by_date(date_str)
            
            # Prepare response
            batch_list = []
            for batch in batches:
                batch_list.append({
                    "batch_id": str(batch.id),
                    "batch_number": batch.batch_number,
                    "status": batch.status.value,
                    "batch_time": batch.batch_time.isoformat(),
                    "total_transactions": batch.total_transactions,
                    "total_amount": batch.total_amount,
                    "completed_transactions": batch.completed_transactions,
                    "failed_transactions": batch.failed_transactions
                })
            
            return {
                "status": "success",
                "date": date_str,
                "batch_count": len(batch_list),
                "batches": batch_list
            }
            
        except Exception as e:
            # Log the error
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def get_pending_batches(
        self,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all pending batches.
        
        Args:
            user_id: Optional user ID for audit logging
            
        Returns:
            Dict[str, Any]: Response with batch list or error
        """
        try:
            # Get pending batches
            batches = self.batch_repository.get_pending_batches()
            
            # Prepare response
            batch_list = []
            for batch in batches:
                batch_list.append({
                    "batch_id": str(batch.id),
                    "batch_number": batch.batch_number,
                    "batch_time": batch.batch_time.isoformat(),
                    "total_transactions": batch.total_transactions,
                    "total_amount": batch.total_amount
                })
            
            return {
                "status": "success",
                "batch_count": len(batch_list),
                "batches": batch_list
            }
            
        except Exception as e:
            # Log the error
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
