"""
RTGS Batch Query Use Case.
"""
from typing import Dict, Any
from uuid import UUID

from ..interfaces.rtgs_batch_repository_interface import RTGSBatchRepositoryInterface
from ..interfaces.rtgs_transaction_repository_interface import RTGSTransactionRepositoryInterface
from ..interfaces.rtgs_rbi_interface_service_interface import RTGSRBIInterfaceServiceInterface
from ...domain.entities.rtgs_batch import RTGSBatch, RTGSBatchStatus


class RTGSBatchQueryUseCase:
    """Use case for querying RTGS batches."""
    
    def __init__(
        self,
        batch_repository: RTGSBatchRepositoryInterface,
        transaction_repository: RTGSTransactionRepositoryInterface,
        rbi_interface_service: RTGSRBIInterfaceServiceInterface
    ):
        """
        Initialize the use case.
        
        Args:
            batch_repository: Repository for batch retrieval
            transaction_repository: Repository for transaction retrieval
            rbi_interface_service: Service for RBI RTGS interface
        """
        self.batch_repository = batch_repository
        self.transaction_repository = transaction_repository
        self.rbi_interface_service = rbi_interface_service
    
    def get_by_id(self, batch_id: UUID) -> Dict[str, Any]:
        """
        Get a batch by ID.
        
        Args:
            batch_id: The batch ID
            
        Returns:
            Dict[str, Any]: Batch details or error
        """
        try:
            # Get batch from repository
            batch = self.batch_repository.get_by_id(batch_id)
            if not batch:
                return {
                    "status": "error",
                    "error_type": "not_found",
                    "message": f"Batch with ID {batch_id} not found"
                }
            
            return self._format_batch_response(batch)
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def get_by_batch_number(self, batch_number: str) -> Dict[str, Any]:
        """
        Get a batch by batch number.
        
        Args:
            batch_number: The batch number
            
        Returns:
            Dict[str, Any]: Batch details or error
        """
        try:
            # Get batch from repository
            batch = self.batch_repository.get_by_batch_number(batch_number)
            if not batch:
                return {
                    "status": "error",
                    "error_type": "not_found",
                    "message": f"Batch with number {batch_number} not found"
                }
            
            return self._format_batch_response(batch)
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def get_by_status(self, status: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get batches by status.
        
        Args:
            status: The batch status
            limit: Maximum number of batches to return
            
        Returns:
            Dict[str, Any]: Batches or error
        """
        try:
            # Get batches from repository
            batches = self.batch_repository.get_by_status(status, limit)
            
            return {
                "status": "success",
                "count": len(batches),
                "batches": [self._format_batch_data(batch) for batch in batches]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def get_by_date_range(self, start_date: str, end_date: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get batches by date range.
        
        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            limit: Maximum number of batches to return
            
        Returns:
            Dict[str, Any]: Batches or error
        """
        try:
            # Get batches from repository
            batches = self.batch_repository.get_by_date_range(start_date, end_date, limit)
            
            return {
                "status": "success",
                "count": len(batches),
                "batches": [self._format_batch_data(batch) for batch in batches]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def get_batch_transactions(self, batch_id: UUID) -> Dict[str, Any]:
        """
        Get all transactions in a batch.
        
        Args:
            batch_id: The batch ID
            
        Returns:
            Dict[str, Any]: Transactions or error
        """
        try:
            # Get batch from repository
            batch = self.batch_repository.get_by_id(batch_id)
            if not batch:
                return {
                    "status": "error",
                    "error_type": "not_found",
                    "message": f"Batch with ID {batch_id} not found"
                }
            
            # Get transactions
            transactions = []
            for tx_id in batch.transaction_ids:
                tx = self.transaction_repository.get_by_id(tx_id)
                if tx:
                    transactions.append(tx)
            
            return {
                "status": "success",
                "batch_id": str(batch.id),
                "batch_number": batch.batch_number,
                "batch_status": batch.status.value,
                "transaction_count": len(transactions),
                "transactions": [
                    {
                        "id": str(tx.id),
                        "transaction_reference": tx.transaction_reference,
                        "utr_number": tx.utr_number,
                        "status": tx.status.value,
                        "amount": tx.payment_details.amount,
                        "beneficiary": tx.payment_details.beneficiary_name,
                        "beneficiary_account": tx.payment_details.beneficiary_account_number
                    }
                    for tx in transactions
                ]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def check_batch_status_with_rbi(self, batch_number: str) -> Dict[str, Any]:
        """
        Check the status of a batch with RBI RTGS system.
        
        Args:
            batch_number: The batch number
            
        Returns:
            Dict[str, Any]: Batch status or error
        """
        try:
            # Get batch from repository
            batch = self.batch_repository.get_by_batch_number(batch_number)
            if not batch:
                return {
                    "status": "error",
                    "error_type": "not_found",
                    "message": f"Batch with number {batch_number} not found"
                }
            
            # Check with RBI only if batch has been sent
            if batch.status in [RTGSBatchStatus.PROCESSING, RTGSBatchStatus.SENT_TO_RBI]:
                rbi_status = self.rbi_interface_service.check_batch_status(batch_number)
                if rbi_status.get("status") == "success":
                    response = self._format_batch_response(batch)
                    response["rbi_status"] = rbi_status.get("batch_status")
                    response["rbi_details"] = rbi_status.get("details", {})
                    return response
            
            return self._format_batch_response(batch)
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def _format_batch_response(self, batch: RTGSBatch) -> Dict[str, Any]:
        """
        Format a batch for API response.
        
        Args:
            batch: The batch to format
            
        Returns:
            Dict[str, Any]: Formatted batch data
        """
        return {
            "status": "success",
            "batch": self._format_batch_data(batch)
        }
    
    def _format_batch_data(self, batch: RTGSBatch) -> Dict[str, Any]:
        """
        Format batch data.
        
        Args:
            batch: The batch to format
            
        Returns:
            Dict[str, Any]: Formatted data
        """
        return {
            "id": str(batch.id),
            "batch_number": batch.batch_number,
            "status": batch.status.value,
            "transaction_count": batch.transaction_count,
            "total_amount": batch.total_amount,
            "scheduled_time": batch.scheduled_time.isoformat(),
            "created_at": batch.created_at.isoformat(),
            "updated_at": batch.updated_at.isoformat(),
            "processed_at": batch.processed_at.isoformat() if batch.processed_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None
        }
