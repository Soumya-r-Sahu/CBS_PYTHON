"""
IMPS Payment Service - Core Banking System

This module provides core business logic for IMPS payments.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import requests

from ..models.imps_model import IMPSTransaction, IMPSPaymentDetails, IMPSStatus, IMPSType
from ..repositories.imps_repository import imps_repository
from ..validators.imps_validators import IMPSValidator
from ..exceptions.imps_exceptions import (
    IMPSException, 
    IMPSValidationError, 
    IMPSTimeoutError,
    IMPSConnectionError, 
    IMPSProcessingError,
    IMPSDuplicateTransactionError
)
from ..config.imps_config import imps_config
from ..utils.imps_utils import generate_imps_reference

# Configure logger
logger = logging.getLogger(__name__)


class IMPSService:
    """Service for processing IMPS transactions."""
    _instance = None
    
    def __new__(cls):
        """Ensure only one instance of IMPSService exists."""
        if cls._instance is None:
            cls._instance = super(IMPSService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the service."""
        self.validator = IMPSValidator()
        self.repository = imps_repository
        self.mock_mode = imps_config.get("mock_mode", True)
        
        if self.mock_mode:
            logger.warning("IMPS service initialized in mock mode. No actual IMPS transfers will occur.")
    
    def create_transaction(self, payment_details: IMPSPaymentDetails, customer_id: str = None) -> IMPSTransaction:
        """
        Create a new IMPS transaction.
        
        Args:
            payment_details: Payment details for the transaction
            customer_id: Customer ID for tracking daily limits (optional)
            
        Returns:
            IMPSTransaction: Created transaction
        """
        # Generate reference number if not provided
        if not payment_details.reference_number:
            payment_details.reference_number = generate_imps_reference(
                mobile_number=payment_details.sender_mobile_number,
                account_number=payment_details.sender_account_number,
                amount=payment_details.amount
            )
        
        # Validate inputs
        self.validator.validate_amount(payment_details.amount)
        
        # Check for duplicates to prevent double payments
        if self.repository.is_duplicate_transaction(
            payment_details.reference_number, 
            payment_details.sender_account_number,
            payment_details.beneficiary_account_number,
            payment_details.amount
        ):
            raise IMPSDuplicateTransactionError(
                f"Duplicate IMPS transaction detected: {payment_details.reference_number}")
        
        if customer_id:
            # Check daily limit if customer ID is provided
            self.validator.validate_daily_limit(customer_id, payment_details.amount)
        
        # Create transaction
        transaction_id = self.repository.create_transaction_id()
        transaction = IMPSTransaction(
            transaction_id=transaction_id,
            payment_details=payment_details,
            status=IMPSStatus.INITIATED
        )
        
        # Validate the full transaction
        self.validator.validate_transaction(transaction)
        
        # Save to repository
        saved_transaction = self.repository.save_transaction(transaction)
        logger.info(f"Created IMPS transaction: {transaction_id}, amount: {payment_details.amount}")
        
        return saved_transaction
    
    def create_p2p_transaction(self, payment_details: IMPSPaymentDetails) -> IMPSTransaction:
        """
        Create a P2P IMPS transaction.
        
        Args:
            payment_details: Payment details for the P2P transaction
            
        Returns:
            IMPSTransaction: Created transaction
        """
        # Ensure transaction is marked as P2P
        payment_details.imps_type = IMPSType.P2P
        
        # Validate P2P specific fields
        if not payment_details.sender_mobile_number or not payment_details.sender_mmid:
            raise IMPSValidationError("Sender mobile number and MMID are required for P2P transfers")
            
        if not payment_details.beneficiary_mobile_number or not payment_details.beneficiary_mmid:
            raise IMPSValidationError("Beneficiary mobile number and MMID are required for P2P transfers")
        
        # Create transaction
        transaction = self.create_transaction(payment_details)
        
        # For P2P, immediately process the transaction
        return self.process_transaction(transaction.transaction_id)
    
    def get_transaction(self, transaction_id: str) -> Optional[IMPSTransaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: Transaction ID to retrieve
            
        Returns:
            Optional[IMPSTransaction]: Transaction if found
        """
        return self.repository.get_transaction(transaction_id)
    
    def process_transaction(self, transaction_id: str) -> IMPSTransaction:
        """
        Process an IMPS transaction.
        
        Args:
            transaction_id: Transaction ID to process
            
        Returns:
            IMPSTransaction: Updated transaction
        """
        # Get transaction
        transaction = self.repository.get_transaction(transaction_id)
        
        # Check if already processed
        if transaction.status != IMPSStatus.INITIATED:
            logger.warning(f"IMPS transaction {transaction_id} already in status {transaction.status}")
            return transaction
        
        try:
            # Validate transaction
            self.validator.validate_transaction(transaction)
            
            # Update status to VALIDATED
            transaction = self.repository.update_transaction_status(
                transaction_id, IMPSStatus.VALIDATED)
            
            # Submit for processing
            if self.mock_mode:
                # Mock processing in development/testing mode
                transaction = self._mock_process_transaction(transaction)
            else:
                # Actual processing in production mode
                transaction = self._submit_transaction_to_npci(transaction)
            
            return transaction
        
        except IMPSValidationError as e:
            # Handle validation errors
            logger.error(f"IMPS validation error: {str(e)}")
            return self.repository.update_transaction_status(
                transaction_id, IMPSStatus.FAILED, str(e))
        
        except Exception as e:
            # Handle other errors
            logger.error(f"Error processing IMPS transaction: {str(e)}", exc_info=True)
            return self.repository.update_transaction_status(
                transaction_id, IMPSStatus.FAILED, f"Internal error: {str(e)}")
    
    def _mock_process_transaction(self, transaction: IMPSTransaction) -> IMPSTransaction:
        """
        Mock IMPS transaction processing for development/testing.
        
        Args:
            transaction: Transaction to process
            
        Returns:
            IMPSTransaction: Updated transaction
        """
        # Update status to PROCESSING
        transaction = self.repository.update_transaction_status(
            transaction.transaction_id, IMPSStatus.PROCESSING)
        
        # For testing, generate a mock RRN
        rrn_part = transaction.transaction_id.split('-')[-1]
        transaction.rrn = f"RRNSIM{rrn_part}"
        
        # Update status to PENDING to simulate waiting for confirmation
        transaction = self.repository.update_transaction_status(
            transaction.transaction_id, IMPSStatus.PENDING)
        
        # In mock mode, mark transaction as completed
        transaction = self.repository.update_transaction_status(
            transaction.transaction_id, IMPSStatus.COMPLETED)
            
        return transaction
    
    def _submit_transaction_to_npci(self, transaction: IMPSTransaction) -> IMPSTransaction:
        """
        Submit transaction to NPCI for processing.
        
        Args:
            transaction: Transaction to submit
            
        Returns:
            IMPSTransaction: Updated transaction
            
        Raises:
            IMPSConnectionError: If connection to NPCI fails
            IMPSTimeoutError: If NPCI request times out
            IMPSProcessingError: If NPCI rejects transaction
        """
        # Update status to PROCESSING
        transaction = self.repository.update_transaction_status(
            transaction.transaction_id, IMPSStatus.PROCESSING)
        
        try:
            # Prepare API payload
            payload = self._prepare_npci_payload(transaction)
            
            # Get API endpoint and credentials
            api_endpoint = imps_config.get("api_endpoint")
            api_key = imps_config.get("api_key")
            api_timeout = imps_config.get("api_timeout_seconds", 30)
            
            # Set headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "X-Transaction-ID": transaction.transaction_id
            }
            
            # Make API call to NPCI
            logger.info(f"Submitting IMPS transaction {transaction.transaction_id} to NPCI")
            response = requests.post(
                f"{api_endpoint}/imps/send",
                json=payload,
                headers=headers,
                timeout=api_timeout
            )
            
            # Process response
            if response.status_code == 200:  # Success
                # Transaction accepted by NPCI
                response_data = response.json()
                rrn = response_data.get("rrn")
                status = response_data.get("status")
                
                # Update transaction with RRN
                transaction.rrn = rrn
                transaction = self.repository.save_transaction(transaction)
                
                # Update status based on NPCI response
                if status == "SUCCESS":
                    transaction = self.repository.update_transaction_status(
                        transaction.transaction_id, IMPSStatus.COMPLETED)
                    logger.info(f"IMPS transaction {transaction.transaction_id} completed successfully with RRN: {rrn}")
                else:
                    transaction = self.repository.update_transaction_status(
                        transaction.transaction_id, IMPSStatus.PENDING)
                    logger.info(f"IMPS transaction {transaction.transaction_id} pending with RRN: {rrn}")
                
            elif response.status_code == 400:  # Bad Request
                # Transaction rejected due to validation errors
                response_data = response.json()
                error_message = response_data.get("error_message", "Unknown validation error")
                
                # Update status to FAILED
                transaction = self.repository.update_transaction_status(
                    transaction.transaction_id, IMPSStatus.FAILED, error_message)
                    
                logger.warning(f"IMPS transaction {transaction.transaction_id} rejected by NPCI: {error_message}")
                raise IMPSProcessingError(error_message)
                
            else:
                # Other error
                error_message = f"NPCI API error: {response.status_code} - {response.text}"
                
                # Update status to FAILED
                transaction = self.repository.update_transaction_status(
                    transaction.transaction_id, IMPSStatus.FAILED, error_message)
                    
                logger.error(error_message)
                raise IMPSConnectionError(error_message)
        
        except requests.exceptions.Timeout:
            # Handle timeout
            error_message = "NPCI API request timed out"
            
            # Update status to FAILED
            transaction = self.repository.update_transaction_status(
                transaction.transaction_id, IMPSStatus.FAILED, error_message)
                
            logger.error(error_message)
            raise IMPSTimeoutError(error_message)
            
        except requests.exceptions.ConnectionError:
            # Handle connection error
            error_message = "Failed to connect to NPCI API"
            
            # Update status to FAILED
            transaction = self.repository.update_transaction_status(
                transaction.transaction_id, IMPSStatus.FAILED, error_message)
                
            logger.error(error_message)
            raise IMPSConnectionError(error_message)
        
        except Exception as e:
            # Handle other errors
            error_message = f"Error submitting IMPS transaction: {str(e)}"
            
            # Update status to FAILED
            transaction = self.repository.update_transaction_status(
                transaction.transaction_id, IMPSStatus.FAILED, error_message)
                
            logger.error(error_message, exc_info=True)
            raise IMPSProcessingError(error_message)
        
        return transaction
    
    def _prepare_npci_payload(self, transaction: IMPSTransaction) -> Dict[str, Any]:
        """
        Prepare IMPS payload for NPCI API.
        
        Args:
            transaction: Transaction to prepare payload for
            
        Returns:
            Dict[str, Any]: API payload
        """
        payment_details = transaction.payment_details
        
        # Base payload
        payload = {
            "transaction_id": transaction.transaction_id,
            "reference_number": payment_details.reference_number,
            "amount": payment_details.amount,
            "remarks": payment_details.remarks,
            "transaction_type": payment_details.imps_type,
            "channel": payment_details.channel,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add sender information
        payload["sender"] = {
            "account_number": payment_details.sender_account_number,
            "ifsc_code": payment_details.sender_ifsc_code,
            "name": payment_details.sender_name
        }
        
        # Add mobile and MMID if available
        if payment_details.sender_mobile_number:
            payload["sender"]["mobile_number"] = payment_details.sender_mobile_number
            
        if payment_details.sender_mmid:
            payload["sender"]["mmid"] = payment_details.sender_mmid
        
        # Add beneficiary information
        payload["beneficiary"] = {
            "name": payment_details.beneficiary_name
        }
        
        # Add account details or mobile+MMID based on transaction type
        if payment_details.imps_type == IMPSType.P2P:
            # P2P uses mobile number and MMID
            payload["beneficiary"]["mobile_number"] = payment_details.beneficiary_mobile_number
            payload["beneficiary"]["mmid"] = payment_details.beneficiary_mmid
        else:
            # Other types use account number and IFSC
            payload["beneficiary"]["account_number"] = payment_details.beneficiary_account_number
            payload["beneficiary"]["ifsc_code"] = payment_details.beneficiary_ifsc_code
            
            # Add mobile if available (optional)
            if payment_details.beneficiary_mobile_number:
                payload["beneficiary"]["mobile_number"] = payment_details.beneficiary_mobile_number
        
        return payload
    
    def check_transaction_status_at_npci(self, transaction_id: str, rrn: str) -> Dict[str, Any]:
        """
        Check transaction status at NPCI.
        
        Args:
            transaction_id: Transaction ID
            rrn: RRN (Reference Retrieval Number) assigned by NPCI
            
        Returns:
            Dict[str, Any]: Status response
        """
        # In mock mode, return mock response
        if self.mock_mode:
            return {
                "status": "SUCCESS",
                "timestamp": datetime.utcnow().isoformat(),
                "rrn": rrn
            }
        
        try:
            # Get API endpoint and credentials
            api_endpoint = imps_config.get("api_endpoint")
            api_key = imps_config.get("api_key")
            api_timeout = imps_config.get("api_timeout_seconds", 30)
            
            # Set headers
            headers = {
                "Authorization": f"Bearer {api_key}",
                "X-Transaction-ID": transaction_id
            }
            
            # Make API call to NPCI
            response = requests.get(
                f"{api_endpoint}/imps/status/{rrn}",
                headers=headers,
                timeout=api_timeout
            )
            
            # Return response data
            return response.json()
        
        except Exception as e:
            logger.error(f"Error checking IMPS status at NPCI: {str(e)}", exc_info=True)
            raise IMPSConnectionError(f"Failed to check status at NPCI: {str(e)}")
    
    def get_transactions_by_status(self, status: IMPSStatus) -> List[IMPSTransaction]:
        """
        Get transactions by status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List[IMPSTransaction]: List of transactions with the given status
        """
        return self.repository.get_transactions_by_status(status)
    
    def get_transactions_by_mobile(self, mobile_number: str) -> List[IMPSTransaction]:
        """
        Get transactions by mobile number.
        
        Args:
            mobile_number: Mobile number to search for
            
        Returns:
            List[IMPSTransaction]: List of transactions for the mobile number
        """
        return self.repository.get_transactions_by_mobile(mobile_number)
    
    def get_transactions_by_account(self, account_number: str) -> List[IMPSTransaction]:
        """
        Get transactions by account number.
        
        Args:
            account_number: Account number to search for
            
        Returns:
            List[IMPSTransaction]: List of transactions for the account
        """
        return self.repository.get_transactions_by_account(account_number)
    
    def retry_transaction(self, transaction_id: str) -> IMPSTransaction:
        """
        Retry a failed IMPS transaction.
        
        Args:
            transaction_id: Transaction ID to retry
            
        Returns:
            IMPSTransaction: Updated transaction
        """
        # Get transaction
        transaction = self.repository.get_transaction(transaction_id)
        
        # Check if eligible for retry
        if transaction.status not in [IMPSStatus.FAILED, IMPSStatus.CANCELLED]:
            logger.warning(f"IMPS transaction {transaction_id} is not eligible for retry: {transaction.status}")
            raise IMPSValidationError(f"Transaction {transaction_id} is not eligible for retry")
        
        # Reset to INITIATED status
        transaction.status = IMPSStatus.INITIATED
        transaction.error_message = None
        transaction.updated_at = datetime.utcnow()
        
        # Save and process
        transaction = self.repository.save_transaction(transaction)
        return self.process_transaction(transaction_id)


# Create singleton instance
imps_service = IMPSService()
