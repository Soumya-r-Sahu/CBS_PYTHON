"""
NEFT Controllers Module for Core Banking System

This module provides controller interfaces for National Electronic Funds Transfer (NEFT) payments 
within the Core Banking System. It handles the business logic for NEFT transactions including
initiation, status checking, and batch processing.

The NEFT system follows the RBI guidelines for electronic funds transfer and provides a secure
and reliable mechanism for interbank transfers across India.

Features:
---------
1. NEFT transfer initiation with comprehensive validation
2. Transaction status tracking throughout the payment lifecycle
3. Batch processing for scheduled NEFT transfers
4. Exception handling with detailed error reporting
5. Audit logging of all operations

Transaction States:
------------------
- INITIATED: Transaction has been created but not yet submitted
- PENDING: Transaction has been submitted to NEFT system
- PROCESSING: Transaction is being processed by the receiving bank
- COMPLETED: Transaction has been successfully completed
- FAILED: Transaction processing failed
- RETURNED: Transaction was returned by the receiving bank

Service Hours:
-------------
NEFT operates in hourly batches from Monday to Friday (8:00 AM to 7:00 PM) 
and the first and third Saturdays of the month (8:00 AM to 1:00 PM).
Transactions submitted after cutoff time are processed in the next batch.

Usage Examples:
--------------
# Initiate a NEFT transfer
payment_data = {
    "sender_account_number": "12345678901",
    "sender_ifsc_code": "ABCD0001234",
    "sender_name": "Raj Kumar",
    "beneficiary_account_number": "98765432109",
    "beneficiary_ifsc_code": "XYZB0004321",
    "beneficiary_name": "Priya Sharma",
    "amount": 25000.00,
    "reference": "Invoice-2023-05-18",
    "remarks": "Salary payment for May 2023"
}
response = NEFTController.initiate_neft_transfer(payment_data, customer_id="CUST123456")

# Check transaction status
status_response = NEFTController.get_transaction_status("NEFT20230518123456")
"""
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, time

from ..models.neft_model import NEFTPaymentDetails, NEFTTransaction, NEFTStatus, NEFTReturnReason
from ..services.neft_service import neft_service
from ..exceptions.neft_exceptions import NEFTException, NEFTValidationError, NEFTLimitExceededException

# Configure logger with appropriate level and formatting
logger = logging.getLogger(__name__)


class NEFTController:
    """
    Controller for NEFT payment operations.
    
    This controller is responsible for handling the business logic related to NEFT payments,
    including transaction initiation, status checking, and batch processing. It acts as an
    intermediary between the API/UI layer and the underlying NEFT services.
    
    All methods are implemented as static methods to allow for stateless operation,
    ensuring thread safety and facilitating horizontal scaling.
    """
    
    @staticmethod
    def initiate_neft_transfer(payment_data: Dict[str, Any], customer_id: str = None) -> Dict[str, Any]:
        """
        Initiate a new NEFT transfer from one bank account to another.
        
        This method validates the payment data, creates a new NEFT transaction,
        and initiates the payment processing. It handles various validation scenarios
        and provides appropriate error responses.
        
        Args:
            payment_data: Dictionary containing the following fields:
                - sender_account_number: Account number of the sender
                - sender_ifsc_code: IFSC code of sender's bank branch
                - sender_account_type: Type of sender's account (SAVINGS, CURRENT, etc.)
                - sender_name: Name of the sender
                - beneficiary_account_number: Account number of the recipient
                - beneficiary_ifsc_code: IFSC code of recipient's bank branch
                - beneficiary_account_type: Type of recipient's account
                - beneficiary_name: Name of the recipient
                - amount: Amount to transfer (must be > 0)
                - reference: Payment reference (optional)
                - remarks: Additional remarks (optional)
            
            customer_id: Unique identifier of the customer initiating the transfer.
                         Used for applying daily/monthly limits and audit trail.
            
        Returns:
            Dict[str, Any]: Response dictionary with the following fields:
                On success:
                - status: "success"
                - transaction_id: Unique identifier for the transaction
                - amount: Transaction amount
                - beneficiary_account: Recipient's account number (masked)
                - beneficiary_ifsc: Recipient's IFSC code
                - transaction_status: Current status of the transaction
                - batch_number: NEFT batch number assigned
                - message: Success message
                
                On error:
                - status: "error"
                - error_type: Type of error (validation, processing, system)
                - message: Detailed error message
                
        Raises:
            No exceptions are propagated to the caller. All exceptions are
            caught and converted to appropriate error responses.
        
        Note:
            This method logs all transactions for audit purposes.
            Transactions above ₹2 lakh are subject to additional verification.
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
            logger.error(f"Unexpected error in NEFT transfer: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }
    
    @staticmethod
    def get_transaction_status(transaction_id: str) -> Dict[str, Any]:
        """
        Get the current status and details of a NEFT transaction.
        
        This method retrieves comprehensive information about a NEFT transaction,
        including its current status, timestamps, and any additional details 
        relevant to its current state (e.g., UTR number for completed transactions 
        or error messages for failed ones).
        
        Args:
            transaction_id: Unique identifier of the NEFT transaction to query
            
        Returns:
            Dict[str, Any]: Response dictionary with the following fields:
                On success:
                - status: "success"
                - transaction_id: Unique identifier for the transaction
                - transaction_status: Current status of the transaction
                - amount: Transaction amount
                - created_at: Timestamp when the transaction was created
                - updated_at: Timestamp when the transaction was last updated
                
                Status-specific fields:
                For COMPLETED transactions:
                - utr_number: Unique Transaction Reference number assigned by RBI
                - completed_at: Timestamp when the transaction was completed
                
                For FAILED/RETURNED transactions:
                - error_message: Detailed error message
                - failed_at/returned_at: Timestamp when the transaction failed/returned
                - return_reason: Reason code for returned transactions
                
                On error:
                - status: "error"
                - error_type: Type of error (not_found, system)
                - message: Detailed error message
                
        Note:
            UTR numbers should be preserved for audit and reconciliation purposes.
            They are the primary reference for any disputes or investigations.
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
            logger.error(f"Error getting NEFT transaction status: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }
    
    @staticmethod
    def process_batch(batch_id: str) -> Dict[str, Any]:
        """
        Process a batch of NEFT transactions.
        
        This method is primarily used by the NEFT scheduler or administrators to
        manually trigger the processing of a specific NEFT batch. It coordinates
        the execution of all transactions in the batch and provides comprehensive
        statistics on the outcome.
        
        NEFT transactions are processed in hourly batches as per RBI guidelines.
        Each batch has a unique identifier and contains multiple transactions that
        were initiated within that batch's time window.
        
        Args:
            batch_id: Unique identifier of the NEFT batch to process
            
        Returns:
            Dict[str, Any]: Response dictionary with the following fields:
                On success:
                - status: "success"
                - batch_id: Unique identifier for the batch
                - batch_status: Current status of the batch (COMPLETED, PARTIAL, FAILED)
                - total_transactions: Total number of transactions in the batch
                - successful_transactions: Number of successfully completed transactions
                - failed_transactions: Number of failed transactions
                - total_amount: Total amount processed in the batch
                - message: Summary message with batch results
                
                On error:
                - status: "error"
                - error_type: Type of error (processing, system)
                - message: Detailed error message
                
        Note:
            This method requires elevated privileges and should only be accessible
            to system administrators or the automated NEFT scheduler.
            
            All batch processing activities are logged for audit purposes.
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
            logger.error(f"Unexpected error processing NEFT batch: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }
