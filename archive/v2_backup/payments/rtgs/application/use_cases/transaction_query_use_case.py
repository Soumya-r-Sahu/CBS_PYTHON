"""
RTGS Transaction Query Use Case.
"""
from typing import Dict, Any, Optional, List
from uuid import UUID

from ..interfaces.rtgs_transaction_repository_interface import RTGSTransactionRepositoryInterface
from ..interfaces.rtgs_rbi_interface_service_interface import RTGSRBIInterfaceServiceInterface
from ...domain.entities.rtgs_transaction import RTGSTransaction, RTGSStatus


class RTGSTransactionQueryUseCase:
    """Use case for querying RTGS transactions."""
    
    def __init__(
        self,
        transaction_repository: RTGSTransactionRepositoryInterface,
        rbi_interface_service: RTGSRBIInterfaceServiceInterface
    ):
        """
        Initialize the use case.
        
        Args:
            transaction_repository: Repository for transaction retrieval
            rbi_interface_service: Service for RBI RTGS interface
        """
        self.transaction_repository = transaction_repository
        self.rbi_interface_service = rbi_interface_service
    
    def get_by_id(self, transaction_id: UUID) -> Dict[str, Any]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: The transaction ID
            
        Returns:
            Dict[str, Any]: Transaction details or error
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
            
            return self._format_transaction_response(transaction)
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def get_by_customer_id(self, customer_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get transactions by customer ID.
        
        Args:
            customer_id: The customer ID
            limit: Maximum number of transactions to return
            
        Returns:
            Dict[str, Any]: Transactions or error
        """
        try:
            # Get transactions from repository
            transactions = self.transaction_repository.get_by_customer_id(customer_id, limit)
            
            return {
                "status": "success",
                "count": len(transactions),
                "transactions": [self._format_transaction_data(tx) for tx in transactions]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def get_by_status(self, status: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get transactions by status.
        
        Args:
            status: The transaction status
            limit: Maximum number of transactions to return
            
        Returns:
            Dict[str, Any]: Transactions or error
        """
        try:
            # Get transactions from repository
            transactions = self.transaction_repository.get_by_status(status, limit)
            
            return {
                "status": "success",
                "count": len(transactions),
                "transactions": [self._format_transaction_data(tx) for tx in transactions]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def get_by_utr_number(self, utr_number: str) -> Dict[str, Any]:
        """
        Get a transaction by UTR number and check its status with RBI.
        
        Args:
            utr_number: The Unique Transaction Reference number
            
        Returns:
            Dict[str, Any]: Transaction details with RBI status or error
        """
        try:
            # Get transaction from repository
            transaction = self.transaction_repository.get_by_utr_number(utr_number)
            if not transaction:
                return {
                    "status": "error",
                    "error_type": "not_found",
                    "message": f"Transaction with UTR number {utr_number} not found"
                }
            
            # Get status from RBI if transaction is in progress
            if transaction.status in [RTGSStatus.PROCESSING, RTGSStatus.PENDING_RBI]:
                rbi_status = self.rbi_interface_service.check_transaction_status(utr_number)
                if rbi_status.get("status") == "success":
                    response = self._format_transaction_response(transaction)
                    response["rbi_status"] = rbi_status.get("transaction_status")
                    response["rbi_details"] = rbi_status.get("details", {})
                    return response
            
            return self._format_transaction_response(transaction)
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def get_by_date_range(self, start_date: str, end_date: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get transactions by date range.
        
        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            limit: Maximum number of transactions to return
            
        Returns:
            Dict[str, Any]: Transactions or error
        """
        try:
            # Get transactions from repository
            transactions = self.transaction_repository.get_by_date_range(start_date, end_date, limit)
            
            return {
                "status": "success",
                "count": len(transactions),
                "transactions": [self._format_transaction_data(tx) for tx in transactions]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "system",
                "message": str(e)
            }
    
    def _format_transaction_response(self, transaction: RTGSTransaction) -> Dict[str, Any]:
        """
        Format a transaction for API response.
        
        Args:
            transaction: The transaction to format
            
        Returns:
            Dict[str, Any]: Formatted transaction data
        """
        return {
            "status": "success",
            "transaction": self._format_transaction_data(transaction)
        }
    
    def _format_transaction_data(self, transaction: RTGSTransaction) -> Dict[str, Any]:
        """
        Format transaction data.
        
        Args:
            transaction: The transaction to format
            
        Returns:
            Dict[str, Any]: Formatted data
        """
        return {
            "id": str(transaction.id),
            "transaction_reference": transaction.transaction_reference,
            "utr_number": transaction.utr_number,
            "status": transaction.status.value,
            "amount": transaction.payment_details.amount,
            "sender": {
                "name": transaction.payment_details.sender_name,
                "account_number": transaction.payment_details.sender_account_number,
                "ifsc_code": transaction.payment_details.sender_ifsc_code,
                "account_type": transaction.payment_details.sender_account_type
            },
            "beneficiary": {
                "name": transaction.payment_details.beneficiary_name,
                "account_number": transaction.payment_details.beneficiary_account_number,
                "ifsc_code": transaction.payment_details.beneficiary_ifsc_code,
                "account_type": transaction.payment_details.beneficiary_account_type
            },
            "payment_reference": transaction.payment_details.payment_reference,
            "remarks": transaction.payment_details.remarks,
            "priority": transaction.payment_details.priority.value if hasattr(transaction.payment_details, 'priority') else None,
            "created_at": transaction.created_at.isoformat(),
            "updated_at": transaction.updated_at.isoformat(),
            "processed_at": transaction.processed_at.isoformat() if transaction.processed_at else None
        }
