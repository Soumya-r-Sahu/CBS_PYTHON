"""
NEFT Transaction Query Use Case.
"""
from typing import Dict, Any, Optional, List
from uuid import UUID

from ...domain.entities.neft_transaction import NEFTTransaction, NEFTStatus
from ..interfaces.neft_transaction_repository_interface import NEFTTransactionRepositoryInterface
from ..interfaces.neft_audit_log_service_interface import NEFTAuditLogServiceInterface


class NEFTTransactionQueryUseCase:
    """Use case for querying NEFT transactions."""
    
    def __init__(
        self,
        transaction_repository: NEFTTransactionRepositoryInterface,
        audit_log_service: NEFTAuditLogServiceInterface
    ):
        """
        Initialize the use case.
        
        Args:
            transaction_repository: Repository for transaction persistence
            audit_log_service: Service for audit logging
        """
        self.transaction_repository = transaction_repository
        self.audit_log_service = audit_log_service
    
    def get_transaction(
        self,
        transaction_id: UUID,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get details of a NEFT transaction.
        
        Args:
            transaction_id: Transaction ID to query
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
                    "message": f"Transaction {transaction_id} not found"
                }
            
            # Prepare response
            response = {
                "status": "success",
                "transaction_id": str(transaction.id),
                "transaction_reference": transaction.transaction_reference,
                "transaction_status": transaction.status.value,
                "amount": transaction.payment_details.amount,
                "sender_account": transaction.payment_details.sender_account_number,
                "sender_name": transaction.payment_details.sender_name,
                "beneficiary_account": transaction.payment_details.beneficiary_account_number,
                "beneficiary_name": transaction.payment_details.beneficiary_name,
                "beneficiary_ifsc": transaction.payment_details.beneficiary_ifsc_code,
                "payment_reference": transaction.payment_details.payment_reference,
                "remarks": transaction.payment_details.remarks,
                "created_at": transaction.created_at.isoformat(),
                "updated_at": transaction.updated_at.isoformat(),
                "batch_number": transaction.batch_number
            }
            
            # Add additional info based on status
            if transaction.status == NEFTStatus.COMPLETED:
                response["utr_number"] = transaction.utr_number
                if transaction.completed_at:
                    response["completed_at"] = transaction.completed_at.isoformat()
            elif transaction.status in [NEFTStatus.FAILED, NEFTStatus.RETURNED]:
                response["error_message"] = transaction.error_message
                if transaction.completed_at:
                    response["failed_at"] = transaction.completed_at.isoformat()
                if transaction.return_reason:
                    response["return_reason"] = transaction.return_reason.value
            
            return response
            
        except Exception as e:
            # Log the error
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def get_customer_transactions(
        self,
        customer_id: str,
        limit: int = 10,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get transactions for a customer.
        
        Args:
            customer_id: Customer ID to query
            limit: Maximum number of transactions to return
            user_id: Optional user ID for audit logging
            
        Returns:
            Dict[str, Any]: Response with transaction list or error
        """
        try:
            # Get transactions
            transactions = self.transaction_repository.get_by_customer_id(customer_id, limit)
            
            # Prepare response
            transaction_list = []
            for tx in transactions:
                transaction_list.append({
                    "transaction_id": str(tx.id),
                    "transaction_reference": tx.transaction_reference,
                    "status": tx.status.value,
                    "amount": tx.payment_details.amount,
                    "beneficiary_name": tx.payment_details.beneficiary_name,
                    "beneficiary_account": tx.payment_details.beneficiary_account_number,
                    "created_at": tx.created_at.isoformat(),
                    "utr_number": tx.utr_number
                })
            
            return {
                "status": "success",
                "customer_id": customer_id,
                "transaction_count": len(transaction_list),
                "transactions": transaction_list
            }
            
        except Exception as e:
            # Log the error
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
