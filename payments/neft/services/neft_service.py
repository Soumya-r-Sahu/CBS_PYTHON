"""
NEFT Service - Core Banking System

This module provides core business logic for NEFT payments.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, time, timedelta
import json
import requests

from ..models.neft_model import NEFTTransaction, NEFTPaymentDetails, NEFTStatus, NEFTBatch
from ..repositories.neft_repository import neft_repository
from ..validators.neft_validators import NEFTValidator
from ..exceptions.neft_exceptions import (
    NEFTException, NEFTValidationError, NEFTTimeoutError, 
    NEFTConnectionError, NEFTProcessingError
)
from ..config.neft_config import neft_config

# Configure logger
logger = logging.getLogger(__name__)


class NEFTService:
    """Service for processing NEFT transactions."""
    _instance = None
    
    def __new__(cls):
        """Ensure only one instance of NEFTService exists."""
        if cls._instance is None:
            cls._instance = super(NEFTService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the service."""
        self.validator = NEFTValidator()
        self.repository = neft_repository
        self.mock_mode = neft_config.get("mock_mode", True)
        
        if self.mock_mode:
            logger.warning("NEFT service initialized in mock mode. No actual NEFT transfers will occur.")
    
    def create_transaction(self, payment_details: NEFTPaymentDetails, customer_id: str = None) -> NEFTTransaction:
        """
        Create a new NEFT transaction.
        
        Args:
            payment_details: Payment details for the transaction
            customer_id: Customer ID for tracking daily limits (optional)
            
        Returns:
            NEFTTransaction: Created transaction
        """
        # Validate inputs
        self.validator.validate_amount(payment_details.amount)
        
        if customer_id:
            # Check daily limit if customer ID is provided
            self.validator.validate_daily_limit(customer_id, payment_details.amount)
        
        # Create transaction
        transaction_id = self.repository.create_transaction_id()
        transaction = NEFTTransaction(
            transaction_id=transaction_id,
            payment_details=payment_details,
            status=NEFTStatus.INITIATED
        )
        
        # Validate the full transaction
        self.validator.validate_transaction(transaction)
        
        # Save to repository
        saved_transaction = self.repository.save_transaction(transaction)
        logger.info(f"Created NEFT transaction: {transaction_id}, amount: {payment_details.amount}")
        
        return saved_transaction
    
    def get_transaction(self, transaction_id: str) -> Optional[NEFTTransaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: Transaction ID to retrieve
            
        Returns:
            Optional[NEFTTransaction]: Transaction if found, None otherwise
        """
        return self.repository.get_transaction(transaction_id)
    
    def process_transaction(self, transaction_id: str) -> NEFTTransaction:
        """
        Process a NEFT transaction (validate and queue for processing).
        
        Args:
            transaction_id: Transaction ID to process
            
        Returns:
            NEFTTransaction: Updated transaction
            
        Raises:
            NEFTException: If transaction cannot be processed
        """
        # Get transaction
        transaction = self.repository.get_transaction(transaction_id)
        if not transaction:
            raise NEFTException(f"Transaction not found: {transaction_id}")
        
        # Check if transaction is in valid state
        if transaction.status != NEFTStatus.INITIATED:
            raise NEFTException(
                f"Transaction {transaction_id} is in {transaction.status} state, "
                "cannot be processed"
            )
        
        # Update status to VALIDATED
        transaction.update_status(NEFTStatus.VALIDATED)
        self.repository.save_transaction(transaction)
        
        # Queue transaction into next available batch
        self._add_to_batch(transaction)
        
        logger.info(f"NEFT transaction processed: {transaction_id}")
        return transaction
    
    def _add_to_batch(self, transaction: NEFTTransaction) -> None:
        """
        Add a transaction to the next available NEFT batch.
        
        Args:
            transaction: Transaction to add to batch
        """
        # Find or create appropriate batch
        next_batch_time = self._calculate_next_batch_time()
        batch_id = self.repository.create_batch_id(next_batch_time)
        
        # Get or create batch
        batch = self.repository.get_batch(batch_id)
        if not batch:
            batch = NEFTBatch(
                batch_id=batch_id,
                batch_time=next_batch_time,
                status="PENDING"
            )
        
        # Add transaction to batch
        if transaction.transaction_id not in batch.transactions:
            batch.transactions.append(transaction.transaction_id)
            batch.total_transactions += 1
            batch.total_amount += transaction.payment_details.amount
        
        # Update transaction with batch information
        transaction.batch_number = batch_id
        self.repository.save_transaction(transaction)
        
        # Save updated batch
        self.repository.save_batch(batch)
        
        logger.debug(
            f"Added transaction {transaction.transaction_id} to batch {batch_id}, "
            f"scheduled for {next_batch_time}"
        )
    
    def _calculate_next_batch_time(self) -> datetime:
        """
        Calculate the next available NEFT batch time.
        
        Returns:
            datetime: Next batch processing time
        """
        now = datetime.utcnow()
        batch_times = neft_config.get("batch_time_intervals", ["00:30"])
        hold_minutes = neft_config.get("hold_time_minutes", 10)
        
        # Convert time strings to datetime objects for today
        batch_datetimes = []
        for batch_time_str in batch_times:
            hours, minutes = map(int, batch_time_str.split(":"))
            batch_dt = datetime.combine(now.date(), time(hours, minutes))
            
            # If batch time is in the past, use tomorrow
            if batch_dt <= now:
                batch_dt += timedelta(days=1)
                
            batch_datetimes.append(batch_dt)
        
        # Sort and find the next available time
        batch_datetimes.sort()
        next_time = batch_datetimes[0]
        
        # Add hold time
        effective_time = now + timedelta(minutes=hold_minutes)
        
        # If effective time is after the first batch, find the next one
        for batch_time in batch_datetimes:
            if batch_time >= effective_time:
                next_time = batch_time
                break
        
        return next_time
    
    def process_batch(self, batch_id: str) -> NEFTBatch:
        """
        Process a NEFT batch.
        
        Args:
            batch_id: Batch ID to process
            
        Returns:
            NEFTBatch: Updated batch
            
        Raises:
            NEFTException: If batch cannot be processed
        """
        # Get batch
        batch = self.repository.get_batch(batch_id)
        if not batch:
            raise NEFTException(f"Batch not found: {batch_id}")
        
        # Check if batch is in valid state
        if batch.status != "PENDING":
            raise NEFTException(
                f"Batch {batch_id} is in {batch.status} state, cannot be processed"
            )
        
        # Update batch status
        batch.status = "PROCESSING"
        self.repository.save_batch(batch)
        
        # Process each transaction in batch
        for tx_id in batch.transactions:
            transaction = self.repository.get_transaction(tx_id)
            if not transaction:
                logger.warning(f"Transaction {tx_id} in batch {batch_id} not found, skipping")
                continue
                
            # Update transaction status
            transaction.update_status(NEFTStatus.PROCESSING)
            self.repository.save_transaction(transaction)
            
            try:
                # In mock mode, simulate RBI processing
                if self.mock_mode:
                    processed_tx = self._mock_process_neft(transaction)
                else:
                    processed_tx = self._send_to_rbi_neft_system(transaction)
                
                # Update transaction with results
                self.repository.save_transaction(processed_tx)
                
                # Update batch stats
                if processed_tx.status == NEFTStatus.COMPLETED:
                    batch.completed_transactions += 1
                elif processed_tx.status in [NEFTStatus.FAILED, NEFTStatus.RETURNED]:
                    batch.failed_transactions += 1
            
            except Exception as e:
                logger.error(f"Error processing NEFT transaction {tx_id} in batch {batch_id}: {str(e)}")
                # Mark transaction as failed
                transaction.update_status(NEFTStatus.FAILED)
                transaction.error_message = str(e)
                self.repository.save_transaction(transaction)
                batch.failed_transactions += 1
        
        # Update batch status
        batch.status = "COMPLETED"
        self.repository.save_batch(batch)
        
        logger.info(f"Processed NEFT batch: {batch_id}, success: {batch.completed_transactions}/{batch.total_transactions}")
        return batch
    
    def _mock_process_neft(self, transaction: NEFTTransaction) -> NEFTTransaction:
        """
        Mock NEFT processing for development/testing.
        
        Args:
            transaction: Transaction to process
            
        Returns:
            NEFTTransaction: Updated transaction
        """
        # Simulate processing delay
        import time
        time.sleep(1)
        
        # Generate UTR number
        import random
        utr = f"UTR{int(time.time())}{random.randint(1000, 9999)}"
        transaction.utr_number = utr
        
        # 90% success rate in mock mode
        if random.random() < 0.9:
            transaction.update_status(NEFTStatus.COMPLETED)
            logger.debug(f"Mock NEFT successful: {transaction.transaction_id}, UTR: {utr}")
        else:
            transaction.update_status(NEFTStatus.FAILED)
            transaction.error_message = "Mock NEFT failure for testing"
            logger.debug(f"Mock NEFT failed: {transaction.transaction_id}")
        
        return transaction
    
    def _send_to_rbi_neft_system(self, transaction: NEFTTransaction) -> NEFTTransaction:
        """
        Send transaction to RBI NEFT system for processing.
        
        Args:
            transaction: Transaction to process
            
        Returns:
            NEFTTransaction: Updated transaction
            
        Raises:
            NEFTConnectionError: If connection to RBI system fails
            NEFTTimeoutError: If request times out
            NEFTProcessingError: If RBI system returns an error
        """
        # In a real implementation, this would connect to the RBI NEFT system
        # via a secure API or file-based interface
        
        try:
            # Prepare request data
            url = neft_config.get("rbi_neft_service_url")
            payment = transaction.payment_details
            
            payload = {
                "transaction_id": transaction.transaction_id,
                "sender": {
                    "account_number": payment.sender_account_number,
                    "ifsc_code": payment.sender_ifsc_code,
                    "account_type": payment.sender_account_type,
                    "name": payment.sender_name
                },
                "beneficiary": {
                    "account_number": payment.beneficiary_account_number,
                    "ifsc_code": payment.beneficiary_ifsc_code,
                    "account_type": payment.beneficiary_account_type,
                    "name": payment.beneficiary_name
                },
                "amount": payment.amount,
                "reference": payment.payment_reference,
                "remarks": payment.remarks
            }
            
            # Set timeouts
            conn_timeout = neft_config.get("connection_timeout_seconds", 30)
            read_timeout = neft_config.get("request_timeout_seconds", 60)
            
            # Send request
            response = requests.post(
                url,
                json=payload,
                timeout=(conn_timeout, read_timeout)
            )
            
            # Process response
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get("status") == "SUCCESS":
                    transaction.update_status(NEFTStatus.COMPLETED)
                    transaction.utr_number = response_data.get("utr_number")
                else:
                    transaction.update_status(NEFTStatus.FAILED)
                    transaction.error_message = response_data.get("error_message", "Unknown error")
            else:
                raise NEFTProcessingError(
                    f"RBI NEFT system returned error: {response.status_code}, {response.text}"
                )
                
        except requests.exceptions.ConnectionError:
            raise NEFTConnectionError("Failed to connect to RBI NEFT system")
        except requests.exceptions.Timeout:
            raise NEFTTimeoutError("Request to RBI NEFT system timed out")
        except Exception as e:
            raise NEFTProcessingError(f"Error processing NEFT transaction: {str(e)}")
        
        return transaction


# Create a singleton instance for import
neft_service = NEFTService()
