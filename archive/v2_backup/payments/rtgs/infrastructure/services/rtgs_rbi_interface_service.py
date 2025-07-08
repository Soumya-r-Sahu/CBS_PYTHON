"""
RBI interface service implementation for RTGS.
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import requests

from ...application.interfaces.rtgs_rbi_interface_service_interface import RTGSRBIInterfaceServiceInterface
from ...domain.entities.rtgs_transaction import RTGSTransaction, RTGSStatus

logger = logging.getLogger(__name__)


class RTGSRBIInterfaceService(RTGSRBIInterfaceServiceInterface):
    """Implementation of the RBI interface service."""
    
    def __init__(self, api_url: str, api_key: str, use_mock: bool = False):
        """
        Initialize the RBI interface service.
        
        Args:
            api_url: The RBI API URL
            api_key: The API key for authentication
            use_mock: Whether to use mock responses (for testing)
        """
        self.api_url = api_url
        self.api_key = api_key
        self.use_mock = use_mock
    
    def send_transaction(self, transaction: RTGSTransaction) -> Dict[str, Any]:
        """
        Send a transaction to RBI.
        
        Args:
            transaction: The transaction to send
            
        Returns:
            Dict[str, Any]: Response from RBI
        """
        if self.use_mock:
            logger.info(f"[MOCK] Sending RTGS transaction {transaction.id} to RBI")
            # Mock a successful response
            return {
                "status": "success",
                "utr_number": f"UTR{transaction.id.hex[:16].upper()}",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Transaction received by RBI"
            }
        
        # Real implementation
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Format transaction data as per RBI API requirements
            payload = {
                "transaction_id": str(transaction.id),
                "transaction_reference": transaction.transaction_reference,
                "sender_details": {
                    "account_number": transaction.payment_details.sender_account_number,
                    "ifsc_code": transaction.payment_details.sender_ifsc_code,
                    "account_type": transaction.payment_details.sender_account_type,
                    "name": transaction.payment_details.sender_name
                },
                "beneficiary_details": {
                    "account_number": transaction.payment_details.beneficiary_account_number,
                    "ifsc_code": transaction.payment_details.beneficiary_ifsc_code,
                    "account_type": transaction.payment_details.beneficiary_account_type,
                    "name": transaction.payment_details.beneficiary_name
                },
                "amount": transaction.payment_details.amount,
                "payment_reference": transaction.payment_details.payment_reference,
                "remarks": transaction.payment_details.remarks,
                "priority": transaction.payment_details.priority.value
            }
            
            # Send request to RBI API
            response = requests.post(
                f"{self.api_url}/rtgs/transactions",
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error sending RTGS transaction to RBI: {str(e)}")
            raise RuntimeError(f"Failed to send transaction to RBI: {str(e)}")
    
    def check_transaction_status(self, utr_number: str) -> Dict[str, Any]:
        """
        Check the status of a transaction with RBI.
        
        Args:
            utr_number: The UTR number assigned by RBI
            
        Returns:
            Dict[str, Any]: Status response from RBI
        """
        if self.use_mock:
            logger.info(f"[MOCK] Checking RTGS transaction status with UTR {utr_number}")
            # Mock a successful response
            return {
                "status": "success",
                "utr_number": utr_number,
                "rbi_status": "COMPLETED",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Transaction processed successfully"
            }
        
        # Real implementation
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Send request to RBI API
            response = requests.get(
                f"{self.api_url}/rtgs/status/{utr_number}",
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error checking RTGS transaction status with RBI: {str(e)}")
            raise RuntimeError(f"Failed to check transaction status with RBI: {str(e)}")
    
    def send_batch(self, batch_transactions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a batch of transactions to RBI.
        
        Args:
            batch_transactions: Batch data with transactions
            
        Returns:
            Dict[str, Any]: Response from RBI
        """
        if self.use_mock:
            logger.info(f"[MOCK] Sending RTGS batch {batch_transactions['batch_number']} to RBI")
            # Mock a successful response
            return {
                "status": "success",
                "batch_id": batch_transactions['batch_number'],
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Batch received by RBI",
                "accepted_count": batch_transactions['transaction_count']
            }
        
        # Real implementation
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Send request to RBI API
            response = requests.post(
                f"{self.api_url}/rtgs/batches",
                headers=headers,
                data=json.dumps(batch_transactions),
                timeout=60
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error sending RTGS batch to RBI: {str(e)}")
            raise RuntimeError(f"Failed to send batch to RBI: {str(e)}")
    
    def check_batch_status(self, batch_number: str) -> Dict[str, Any]:
        """
        Check the status of a batch with RBI.
        
        Args:
            batch_number: The batch number
            
        Returns:
            Dict[str, Any]: Status response from RBI
        """
        if self.use_mock:
            logger.info(f"[MOCK] Checking RTGS batch status for {batch_number}")
            # Mock a successful response
            return {
                "status": "success",
                "batch_id": batch_number,
                "rbi_status": "PROCESSED",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Batch processed successfully",
                "successful_count": 10,
                "failed_count": 0
            }
        
        # Real implementation
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Send request to RBI API
            response = requests.get(
                f"{self.api_url}/rtgs/batches/{batch_number}/status",
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error checking RTGS batch status with RBI: {str(e)}")
            raise RuntimeError(f"Failed to check batch status with RBI: {str(e)}")
