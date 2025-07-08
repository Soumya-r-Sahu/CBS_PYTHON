"""
RTGS Payment Service - Core Banking System

This module provides core business logic for RTGS payments.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import requests

from ..models.rtgs_model import RTGSTransaction, RTGSPaymentDetails, RTGSStatus
from ..repositories.rtgs_repository import rtgs_repository
from ..validators.rtgs_validators import RTGSValidator
from ..exceptions.rtgs_exceptions import (
    RTGSException, RTGSValidationError, RTGSTimeoutError, 
    RTGSConnectionError, RTGSProcessingError
)
from ..config.rtgs_config import rtgs_config

# Configure logger
logger = logging.getLogger(__name__)


class RTGSService:
    """Service for processing RTGS transactions."""
    _instance = None
    
    def __new__(cls):
        """Ensure only one instance of RTGSService exists."""
        if cls._instance is None:
            cls._instance = super(RTGSService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the service."""
        self.validator = RTGSValidator()
        self.repository = rtgs_repository
        self.mock_mode = rtgs_config.get("mock_mode", True)
        
        if self.mock_mode:
            logger.warning("RTGS service initialized in mock mode. No actual RTGS transfers will occur.")
    
    def create_transaction(self, payment_details: RTGSPaymentDetails, customer_id: str = None) -> RTGSTransaction:
        """
        Create a new RTGS transaction.
        
        Args:
            payment_details: Payment details for the transaction
            customer_id: Customer ID for tracking daily limits (optional)
            
        Returns:
            RTGSTransaction: Created transaction
        """
        # Validate inputs
        self.validator.validate_amount(payment_details.amount)
        
        if customer_id:
            # Check daily limit if customer ID is provided
            self.validator.validate_daily_limit(customer_id, payment_details.amount)
        
        # Create transaction
        transaction_id = self.repository.create_transaction_id()
        transaction = RTGSTransaction(
            transaction_id=transaction_id,
            payment_details=payment_details,
            status=RTGSStatus.INITIATED
        )
        
        # Validate the full transaction
        self.validator.validate_transaction(transaction)
        
        # Save to repository
        saved_transaction = self.repository.save_transaction(transaction)
        logger.info(f"Created RTGS transaction: {transaction_id}, amount: {payment_details.amount}")
        
        return saved_transaction
    
    def get_transaction(self, transaction_id: str) -> Optional[RTGSTransaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: Transaction ID to retrieve
            
        Returns:
            Optional[RTGSTransaction]: Transaction if found, None otherwise
        """
        return self.repository.get_transaction(transaction_id)
    
    def process_transaction(self, transaction_id: str) -> RTGSTransaction:
        """
        Process an RTGS transaction (validate and submit).
        
        Args:
            transaction_id: Transaction ID to process
            
        Returns:
            RTGSTransaction: Updated transaction
        """
        # Get transaction
        transaction = self.repository.get_transaction(transaction_id)
        
        # Check if already processed
        if transaction.status != RTGSStatus.INITIATED:
            logger.warning(f"RTGS transaction {transaction_id} already in status {transaction.status}")
            return transaction
        
        try:
            # Validate transaction
            self.validator.validate_transaction(transaction)
            
            # Update status to VALIDATED
            transaction = self.repository.update_transaction_status(
                transaction_id, RTGSStatus.VALIDATED)
            
            # Submit for processing
            if self.mock_mode:
                # Mock processing in development/testing mode
                transaction = self._mock_process_transaction(transaction)
            else:
                # Actual processing in production mode
                transaction = self._submit_transaction_to_rbi(transaction)
            
            return transaction
        
        except RTGSValidationError as e:
            # Handle validation errors
            logger.error(f"RTGS validation error: {str(e)}")
            return self.repository.update_transaction_status(
                transaction_id, RTGSStatus.FAILED, str(e))
        
        except Exception as e:
            # Handle other errors
            logger.error(f"Error processing RTGS transaction: {str(e)}", exc_info=True)
            return self.repository.update_transaction_status(
                transaction_id, RTGSStatus.FAILED, f"Internal error: {str(e)}")
    
    def _mock_process_transaction(self, transaction: RTGSTransaction) -> RTGSTransaction:
        """
        Mock RTGS transaction processing for development/testing.
        
        Args:
            transaction: Transaction to process
            
        Returns:
            RTGSTransaction: Updated transaction
        """
        # Update status to PROCESSING
        transaction = self.repository.update_transaction_status(
            transaction.transaction_id, RTGSStatus.PROCESSING)
        
        # For testing, generate a mock UTR number
        utr_part = transaction.transaction_id.split('-')[-1]
        transaction.utr_number = f"TUTRSIM{utr_part}"
        
        # Update status to PENDING_RBI to simulate waiting for central bank
        transaction = self.repository.update_transaction_status(
            transaction.transaction_id, RTGSStatus.PENDING_RBI)
        
        # In mock mode, mark transaction as completed
        transaction = self.repository.update_transaction_status(
            transaction.transaction_id, RTGSStatus.COMPLETED)
            
        return transaction
    
    def _submit_transaction_to_rbi(self, transaction: RTGSTransaction) -> RTGSTransaction:
        """
        Submit transaction to RBI for processing.
        
        Args:
            transaction: Transaction to submit
            
        Returns:
            RTGSTransaction: Updated transaction
            
        Raises:
            RTGSConnectionError: If connection to RBI fails
            RTGSTimeoutError: If RBI request times out
            RTGSProcessingError: If RBI rejects transaction
        """
        # Update status to PROCESSING
        transaction = self.repository.update_transaction_status(
            transaction.transaction_id, RTGSStatus.PROCESSING)
        
        try:
            # Prepare API payload
            payload = self._prepare_rbi_payload(transaction)
            
            # Get API endpoint and credentials
            api_endpoint = rtgs_config.get("api_endpoint")
            api_key = rtgs_config.get("api_key")
            api_timeout = rtgs_config.get("api_timeout_seconds", 30)
            
            # Set headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "X-Transaction-ID": transaction.transaction_id
            }
            
            # Make API call to RBI
            logger.info(f"Submitting RTGS transaction {transaction.transaction_id} to RBI")
            response = requests.post(
                f"{api_endpoint}/rtgs/transactions",
                json=payload,
                headers=headers,
                timeout=api_timeout
            )
            
            # Process response
            if response.status_code == 202:  # Accepted
                # Transaction accepted by RBI
                response_data = response.json()
                utr_number = response_data.get("utr_number")
                
                # Update transaction with UTR
                transaction.utr_number = utr_number
                transaction = self.repository.save_transaction(transaction)
                
                # Update status to PENDING_RBI
                transaction = self.repository.update_transaction_status(
                    transaction.transaction_id, RTGSStatus.PENDING_RBI)
                    
                logger.info(f"RTGS transaction {transaction.transaction_id} accepted by RBI with UTR: {utr_number}")
                
            elif response.status_code == 400:  # Bad Request
                # Transaction rejected due to validation errors
                response_data = response.json()
                error_message = response_data.get("error_message", "Unknown validation error")
                
                # Update status to FAILED
                transaction = self.repository.update_transaction_status(
                    transaction.transaction_id, RTGSStatus.FAILED, error_message)
                    
                logger.warning(f"RTGS transaction {transaction.transaction_id} rejected by RBI: {error_message}")
                raise RTGSProcessingError(error_message)
                
            else:
                # Other error
                error_message = f"RBI API error: {response.status_code} - {response.text}"
                
                # Update status to FAILED
                transaction = self.repository.update_transaction_status(
                    transaction.transaction_id, RTGSStatus.FAILED, error_message)
                    
                logger.error(error_message)
                raise RTGSConnectionError(error_message)
        
        except requests.exceptions.Timeout:
            # Handle timeout
            error_message = "RBI API request timed out"
            
            # Update status to FAILED
            transaction = self.repository.update_transaction_status(
                transaction.transaction_id, RTGSStatus.FAILED, error_message)
                
            logger.error(error_message)
            raise RTGSTimeoutError(error_message)
            
        except requests.exceptions.ConnectionError:
            # Handle connection error
            error_message = "Failed to connect to RBI API"
            
            # Update status to FAILED
            transaction = self.repository.update_transaction_status(
                transaction.transaction_id, RTGSStatus.FAILED, error_message)
                
            logger.error(error_message)
            raise RTGSConnectionError(error_message)
        
        except Exception as e:
            # Handle other errors
            error_message = f"Error submitting RTGS transaction: {str(e)}"
            
            # Update status to FAILED
            transaction = self.repository.update_transaction_status(
                transaction.transaction_id, RTGSStatus.FAILED, error_message)
                
            logger.error(error_message, exc_info=True)
            raise RTGSProcessingError(error_message)
        
        return transaction
    
    def _prepare_rbi_payload(self, transaction: RTGSTransaction) -> Dict[str, Any]:
        """
        Prepare RTGS payload for RBI API.
        
        Args:
            transaction: Transaction to prepare payload for
            
        Returns:
            Dict[str, Any]: API payload
        """
        payment_details = transaction.payment_details
        
        return {
            "transaction_id": transaction.transaction_id,
            "remitter": {
                "account_number": payment_details.sender_account_number,
                "ifsc_code": payment_details.sender_ifsc_code,
                "account_type": payment_details.sender_account_type,
                "name": payment_details.sender_name
            },
            "beneficiary": {
                "account_number": payment_details.beneficiary_account_number,
                "ifsc_code": payment_details.beneficiary_ifsc_code,
                "account_type": payment_details.beneficiary_account_type,
                "name": payment_details.beneficiary_name
            },
            "amount": payment_details.amount,
            "reference": payment_details.payment_reference,
            "remarks": payment_details.remarks,
            "purpose_code": payment_details.purpose_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def check_transaction_status_at_rbi(self, transaction_id: str, utr_number: str) -> Dict[str, Any]:
        """
        Check transaction status at RBI.
        
        Args:
            transaction_id: Transaction ID
            utr_number: UTR number assigned by RBI
            
        Returns:
            Dict[str, Any]: Status response
        """
        # TODO: Implement actual RBI status check API call
        # For now, return mock response
        if self.mock_mode:
            return {
                "status": "SETTLED",
                "settlement_time": datetime.utcnow().isoformat(),
                "utr_number": utr_number
            }
        else:
            try:
                # Get API endpoint and credentials
                api_endpoint = rtgs_config.get("api_endpoint")
                api_key = rtgs_config.get("api_key")
                api_timeout = rtgs_config.get("api_timeout_seconds", 30)
                
                # Set headers
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "X-Transaction-ID": transaction_id
                }
                
                # Make API call to RBI
                response = requests.get(
                    f"{api_endpoint}/rtgs/status/{utr_number}",
                    headers=headers,
                    timeout=api_timeout
                )
                
                # Return response data
                return response.json()
            
            except Exception as e:
                logger.error(f"Error checking RTGS status at RBI: {str(e)}", exc_info=True)
                raise RTGSConnectionError(f"Failed to check status at RBI: {str(e)}")
    
    def get_customer_transactions(self, customer_id: str) -> List[RTGSTransaction]:
        """
        Get all transactions for a customer.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            List[RTGSTransaction]: List of customer transactions
        """
        # Call repository method
        return self.repository.get_transactions_by_customer(customer_id)


# Create singleton instance
rtgs_service = RTGSService()
