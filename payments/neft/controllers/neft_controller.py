"""
NEFT Controllers - Core Banking System

This module provides controller interfaces for NEFT payments.
"""
import logging
from typing import Dict, Any, List, Optional

from ..models.neft_model import NEFTPaymentDetails, NEFTTransaction, NEFTStatus
from ..services.neft_service import neft_service
from ..exceptions.neft_exceptions import NEFTException, NEFTValidationError

# Configure logger
logger = logging.getLogger(__name__)


class NEFTController:
    """Controller for NEFT payment operations."""
    
    @staticmethod
    def initiate_neft_transfer(payment_data: Dict[str, Any], customer_id: str = None) -> Dict[str, Any]:
        """
        Initiate a new NEFT transfer.
        
        Args:
            payment_data: Payment details
            customer_id: Customer ID for tracking daily limits (optional)
            
        Returns:
            Dict[str, Any]: Response with transaction details
        """
        logger.info(f"Initiating NEFT transfer for customer {customer_id}")
        
        try:
            # Extract payment details
            payment_details = NEFTPaymentDetails(
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
            
            # Create and process transaction
            transaction = neft_service.create_transaction(payment_details, customer_id)
            processed_tx = neft_service.process_transaction(transaction.transaction_id)
            
            # Prepare response
            return {
                "status": "success",
                "transaction_id": transaction.transaction_id,
                "amount": payment_details.amount,
                "beneficiary_account": payment_details.beneficiary_account_number,
                "beneficiary_ifsc": payment_details.beneficiary_ifsc_code,
                "transaction_status": processed_tx.status.value,
                "batch_number": processed_tx.batch_number,
                "message": "NEFT transfer initiated successfully"
            }
            
        except NEFTValidationError as e:
            logger.warning(f"NEFT validation error: {str(e)}")
            return {
                "status": "error",
                "error_type": "validation",
                "message": str(e)
            }
        except NEFTException as e:
            logger.error(f"NEFT processing error: {str(e)}")
            return {
                "status": "error",
                "error_type": "processing",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error in NEFT transfer: {str(e)}")
            return {
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }
    
    @staticmethod
    def get_transaction_status(transaction_id: str) -> Dict[str, Any]:
        """
        Get status of a NEFT transaction.
        
        Args:
            transaction_id: Transaction ID to query
            
        Returns:
            Dict[str, Any]: Response with transaction status
        """
        logger.info(f"Getting status for NEFT transaction {transaction_id}")
        
        try:
            transaction = neft_service.get_transaction(transaction_id)
            
            if not transaction:
                return {
                    "status": "error",
                    "error_type": "not_found",
                    "message": f"Transaction {transaction_id} not found"
                }
            
            # Prepare response
            response = {
                "status": "success",
                "transaction_id": transaction.transaction_id,
                "transaction_status": transaction.status.value,
                "amount": transaction.payment_details.amount,
                "created_at": transaction.created_at.isoformat(),
                "updated_at": transaction.updated_at.isoformat()
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
            logger.error(f"Error getting NEFT transaction status: {str(e)}")
            return {
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }
    
    @staticmethod
    def process_batch(batch_id: str) -> Dict[str, Any]:
        """
        Process a NEFT batch.
        
        Args:
            batch_id: Batch ID to process
            
        Returns:
            Dict[str, Any]: Response with batch processing results
        """
        logger.info(f"Processing NEFT batch {batch_id}")
        
        try:
            batch = neft_service.process_batch(batch_id)
            
            return {
                "status": "success",
                "batch_id": batch.batch_id,
                "batch_status": batch.status,
                "total_transactions": batch.total_transactions,
                "successful_transactions": batch.completed_transactions,
                "failed_transactions": batch.failed_transactions,
                "total_amount": batch.total_amount,
                "message": f"NEFT batch processed: {batch.completed_transactions}/{batch.total_transactions} successful"
            }
            
        except NEFTException as e:
            logger.error(f"Error processing NEFT batch: {str(e)}")
            return {
                "status": "error",
                "error_type": "processing",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error processing NEFT batch: {str(e)}")
            return {
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }
