"""
NEFT RBI Interface Service.
Implementation of the NEFTRbiInterfaceServiceInterface for communicating with RBI systems.
"""
import logging
import time
import random
import requests
from typing import List, Dict, Any, Tuple
from datetime import datetime

from ...domain.entities.neft_transaction import NEFTTransaction, NEFTStatus
from ...domain.entities.neft_batch import NEFTBatch, NEFTBatchStatus
from ...application.interfaces.neft_rbi_interface_service_interface import NEFTRbiInterfaceServiceInterface


class NEFTRbiInterfaceService(NEFTRbiInterfaceServiceInterface):
    """Implementation of NEFT RBI interface service."""
    
    def __init__(self, config: Dict[str, Any], mock_mode: bool = True):
        """
        Initialize the service.
        
        Args:
            config: Configuration dictionary with RBI connection settings
            mock_mode: Whether to run in mock mode (no actual RBI calls)
        """
        self.mock_mode = mock_mode
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration
        self.rbi_url = config.get("rbi_neft_service_url", "https://rbi-neft-api.example.com")
        self.connection_timeout = config.get("connection_timeout_seconds", 30)
        self.request_timeout = config.get("request_timeout_seconds", 60)
        self.api_key = config.get("rbi_api_key", "mock_api_key")
        
        if self.mock_mode:
            self.logger.warning("RBI Interface Service initialized in mock mode. No actual RBI calls will be made.")
    
    def submit_transaction(self, transaction: NEFTTransaction) -> NEFTTransaction:
        """
        Submit a transaction to the RBI NEFT system.
        
        Args:
            transaction: The transaction to submit
            
        Returns:
            NEFTTransaction: The updated transaction with RBI response
        """
        if self.mock_mode:
            return self._mock_submit_transaction(transaction)
        
        try:
            # Prepare request data
            payment = transaction.payment_details
            
            payload = {
                "transaction_id": str(transaction.id),
                "transaction_reference": transaction.transaction_reference,
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
            
            # Set headers
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "X-Originating-Bank": self.config.get("bank_code", "MOCK1")
            }
            
            # Send request
            response = requests.post(
                f"{self.rbi_url}/transactions",
                json=payload,
                headers=headers,
                timeout=(self.connection_timeout, self.request_timeout)
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
                self.logger.error(f"RBI NEFT system returned error: {response.status_code}, {response.text}")
                transaction.update_status(NEFTStatus.FAILED)
                transaction.error_message = f"RBI system error: {response.status_code}"
        
        except requests.exceptions.ConnectionError:
            transaction.update_status(NEFTStatus.FAILED)
            transaction.error_message = "Failed to connect to RBI NEFT system"
            self.logger.error("Connection error to RBI system")
            
        except requests.exceptions.Timeout:
            transaction.update_status(NEFTStatus.FAILED)
            transaction.error_message = "Request to RBI NEFT system timed out"
            self.logger.error("Request timeout to RBI system")
            
        except Exception as e:
            transaction.update_status(NEFTStatus.FAILED)
            transaction.error_message = f"Error processing NEFT transaction: {str(e)}"
            self.logger.error(f"Error in RBI interface: {str(e)}")
        
        return transaction
    
    def submit_batch(
        self, 
        batch: NEFTBatch, 
        transactions: List[NEFTTransaction]
    ) -> Tuple[NEFTBatch, List[NEFTTransaction]]:
        """
        Submit a batch of transactions to the RBI NEFT system.
        
        Args:
            batch: The batch to submit
            transactions: The transactions in the batch
            
        Returns:
            tuple[NEFTBatch, list[NEFTTransaction]]: The updated batch and transactions
        """
        if self.mock_mode:
            return self._mock_submit_batch(batch, transactions)
        
        try:
            # Update batch status
            batch.update_status(NEFTBatchStatus.SUBMITTED)
            
            # Prepare batch data
            transaction_list = []
            for tx in transactions:
                payment = tx.payment_details
                transaction_list.append({
                    "transaction_id": str(tx.id),
                    "transaction_reference": tx.transaction_reference,
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
                })
            
            payload = {
                "batch_id": str(batch.id),
                "batch_number": batch.batch_number,
                "batch_time": batch.batch_time.isoformat(),
                "total_transactions": batch.total_transactions,
                "total_amount": batch.total_amount,
                "transactions": transaction_list
            }
            
            # Set headers
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "X-Originating-Bank": self.config.get("bank_code", "MOCK1")
            }
            
            # Send request
            response = requests.post(
                f"{self.rbi_url}/batches",
                json=payload,
                headers=headers,
                timeout=(self.connection_timeout, self.request_timeout)
            )
            
            # Process response
            if response.status_code == 200:
                response_data = response.json()
                
                # Process individual transaction results
                tx_results = response_data.get("transaction_results", [])
                tx_map = {str(tx.id): tx for tx in transactions}
                
                for result in tx_results:
                    tx_id = result.get("transaction_id")
                    if tx_id in tx_map:
                        tx = tx_map[tx_id]
                        
                        if result.get("status") == "SUCCESS":
                            tx.update_status(NEFTStatus.COMPLETED)
                            tx.utr_number = result.get("utr_number")
                            batch.record_transaction_result(True)
                        else:
                            tx.update_status(NEFTStatus.FAILED)
                            tx.error_message = result.get("error_message", "Unknown error")
                            batch.record_transaction_result(False)
            else:
                self.logger.error(f"RBI NEFT system returned batch error: {response.status_code}, {response.text}")
                
                # Mark all transactions as failed
                for tx in transactions:
                    tx.update_status(NEFTStatus.FAILED)
                    tx.error_message = f"RBI batch submission error: {response.status_code}"
                    batch.record_transaction_result(False)
        
        except Exception as e:
            self.logger.error(f"Error in RBI batch interface: {str(e)}")
            
            # Mark all transactions as failed
            for tx in transactions:
                tx.update_status(NEFTStatus.FAILED)
                tx.error_message = f"RBI interface error: {str(e)}"
                batch.record_transaction_result(False)
        
        return batch, transactions
    
    def check_transaction_status(self, utr_number: str) -> Dict[str, Any]:
        """
        Check the status of a transaction with the RBI NEFT system.
        
        Args:
            utr_number: UTR number assigned by RBI
            
        Returns:
            dict: Status response from RBI
        """
        if self.mock_mode:
            return self._mock_check_transaction_status(utr_number)
        
        try:
            # Set headers
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "X-Originating-Bank": self.config.get("bank_code", "MOCK1")
            }
            
            # Send request
            response = requests.get(
                f"{self.rbi_url}/transactions/{utr_number}/status",
                headers=headers,
                timeout=(self.connection_timeout, self.request_timeout)
            )
            
            # Process response
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"RBI NEFT system returned error on status check: {response.status_code}, {response.text}")
                return {
                    "status": "ERROR",
                    "error_message": f"RBI system error: {response.status_code}"
                }
        
        except Exception as e:
            self.logger.error(f"Error checking transaction status with RBI: {str(e)}")
            return {
                "status": "ERROR",
                "error_message": f"RBI interface error: {str(e)}"
            }
    
    def check_batch_status(self, batch_number: str) -> Dict[str, Any]:
        """
        Check the status of a batch with the RBI NEFT system.
        
        Args:
            batch_number: Batch number
            
        Returns:
            dict: Status response from RBI
        """
        if self.mock_mode:
            return self._mock_check_batch_status(batch_number)
        
        try:
            # Set headers
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "X-Originating-Bank": self.config.get("bank_code", "MOCK1")
            }
            
            # Send request
            response = requests.get(
                f"{self.rbi_url}/batches/{batch_number}/status",
                headers=headers,
                timeout=(self.connection_timeout, self.request_timeout)
            )
            
            # Process response
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"RBI NEFT system returned error on batch status check: {response.status_code}, {response.text}")
                return {
                    "status": "ERROR",
                    "error_message": f"RBI system error: {response.status_code}"
                }
        
        except Exception as e:
            self.logger.error(f"Error checking batch status with RBI: {str(e)}")
            return {
                "status": "ERROR",
                "error_message": f"RBI interface error: {str(e)}"
            }
    
    def _mock_submit_transaction(self, transaction: NEFTTransaction) -> NEFTTransaction:
        """
        Mock implementation of transaction submission for testing.
        
        Args:
            transaction: The transaction to submit
            
        Returns:
            NEFTTransaction: The updated transaction
        """
        # Simulate processing delay
        time.sleep(0.5)
        
        # Generate UTR number
        utr = f"UTR{int(time.time())}{random.randint(1000, 9999)}"
        
        # 90% success rate in mock mode
        if random.random() < 0.9:
            transaction.update_status(NEFTStatus.COMPLETED)
            transaction.utr_number = utr
            self.logger.debug(f"Mock NEFT successful: {transaction.id}, UTR: {utr}")
        else:
            transaction.update_status(NEFTStatus.FAILED)
            transaction.error_message = "Mock NEFT failure for testing"
            self.logger.debug(f"Mock NEFT failed: {transaction.id}")
        
        return transaction
    
    def _mock_submit_batch(
        self, 
        batch: NEFTBatch, 
        transactions: List[NEFTTransaction]
    ) -> Tuple[NEFTBatch, List[NEFTTransaction]]:
        """
        Mock implementation of batch submission for testing.
        
        Args:
            batch: The batch to submit
            transactions: The transactions in the batch
            
        Returns:
            tuple[NEFTBatch, list[NEFTTransaction]]: The updated batch and transactions
        """
        # Update batch status
        batch.update_status(NEFTBatchStatus.SUBMITTED)
        
        # Simulate processing delay
        time.sleep(1)
        
        # Process each transaction
        for tx in transactions:
            # Generate UTR number
            utr = f"UTR{int(time.time())}{random.randint(1000, 9999)}"
            
            # 90% success rate in mock mode
            if random.random() < 0.9:
                tx.update_status(NEFTStatus.COMPLETED)
                tx.utr_number = utr
                batch.record_transaction_result(True)
                self.logger.debug(f"Mock NEFT batch tx successful: {tx.id}, UTR: {utr}")
            else:
                tx.update_status(NEFTStatus.FAILED)
                tx.error_message = "Mock NEFT batch failure for testing"
                batch.record_transaction_result(False)
                self.logger.debug(f"Mock NEFT batch tx failed: {tx.id}")
        
        return batch, transactions
    
    def _mock_check_transaction_status(self, utr_number: str) -> Dict[str, Any]:
        """
        Mock implementation of transaction status check for testing.
        
        Args:
            utr_number: UTR number assigned by RBI
            
        Returns:
            dict: Status response from mock RBI
        """
        # Simulate processing delay
        time.sleep(0.2)
        
        # 95% success rate for status checks
        if random.random() < 0.95:
            return {
                "status": "SUCCESS",
                "utr_number": utr_number,
                "processed_at": datetime.now().isoformat(),
                "beneficiary_bank_code": "MOCK2",
                "is_settled": True
            }
        else:
            return {
                "status": "ERROR",
                "error_message": "Mock error checking transaction status"
            }
    
    def _mock_check_batch_status(self, batch_number: str) -> Dict[str, Any]:
        """
        Mock implementation of batch status check for testing.
        
        Args:
            batch_number: Batch number
            
        Returns:
            dict: Status response from mock RBI
        """
        # Simulate processing delay
        time.sleep(0.2)
        
        # 95% success rate for status checks
        if random.random() < 0.95:
            return {
                "status": "SUCCESS",
                "batch_number": batch_number,
                "processed_at": datetime.now().isoformat(),
                "total_transactions": random.randint(5, 20),
                "successful_transactions": random.randint(5, 15),
                "failed_transactions": random.randint(0, 5)
            }
        else:
            return {
                "status": "ERROR",
                "error_message": "Mock error checking batch status"
            }
