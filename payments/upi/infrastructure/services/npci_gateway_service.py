"""
NPCI Gateway Service for UPI transactions.

This service handles communication with the NPCI gateway for processing UPI transactions.
"""
import logging
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from ...domain.entities.upi_transaction import UpiTransaction, UpiTransactionStatus
from ...application.interfaces.external_payment_gateway_interface import ExternalPaymentGatewayInterface
from ...domain.exceptions.gateway_exceptions import GatewayConnectionError, GatewayTimeoutError, GatewayAuthenticationError


class NpciGatewayService(ExternalPaymentGatewayInterface):
    """Implementation of NPCI Gateway Service for UPI transactions."""
    
    def __init__(
        self, 
        gateway_url: str,
        merchant_id: str,
        timeout_seconds: int = 30,
        use_mock: bool = False
    ):
        """
        Initialize with NPCI gateway credentials.
        
        Args:
            gateway_url: URL of the NPCI gateway
            merchant_id: Merchant ID for authentication
            timeout_seconds: Timeout in seconds for API calls
            use_mock: Whether to use mock responses (for development/testing)
        """
        self.gateway_url = gateway_url
        self.merchant_id = merchant_id
        self.timeout_seconds = timeout_seconds
        self.use_mock = use_mock
        self.logger = logging.getLogger(__name__)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for NPCI API requests."""
        return {
            'Content-Type': 'application/json',
            'X-Merchant-ID': self.merchant_id,
            'X-Request-Timestamp': datetime.now().isoformat()
        }
    
    def _mock_response(self, transaction: UpiTransaction) -> Dict[str, Any]:
        """Generate a mock response for testing purposes."""
        self.logger.info(f"Generating mock response for transaction {transaction.transaction_id}")
        
        # Simulate success for most transactions, failure for certain amounts
        is_success = transaction.amount != 123.45  # Special test amount that always fails
        
        if is_success:
            return {
                'status': 'SUCCESS',
                'reference_id': f"NPCI-{transaction.transaction_id}",
                'timestamp': datetime.now().isoformat(),
                'gateway_fee': round(transaction.amount * 0.0005, 2),  # 0.05% fee
                'message': 'Transaction processed successfully'
            }
        else:
            return {
                'status': 'FAILED',
                'reference_id': f"NPCI-{transaction.transaction_id}",
                'timestamp': datetime.now().isoformat(),
                'error_code': 'INSUFFICIENT_FUNDS',
                'message': 'Insufficient funds in sender account'
            }
    
    def process_transaction(self, transaction: UpiTransaction) -> Dict[str, Any]:
        """
        Process a UPI transaction through the NPCI gateway.
        
        Args:
            transaction: The UPI transaction to process
            
        Returns:
            Dictionary with the gateway response
            
        Raises:
            GatewayConnectionError: If there's a connection error
            GatewayTimeoutError: If the gateway doesn't respond in time
            GatewayAuthenticationError: If authentication fails
        """
        self.logger.info(f"Processing transaction {transaction.transaction_id} through NPCI gateway")
        
        # Use mock response if configured to do so
        if self.use_mock:
            self.logger.info("Using mock NPCI gateway response")
            return self._mock_response(transaction)
        
        # Prepare request payload
        payload = {
            'transaction_id': str(transaction.transaction_id),
            'sender_vpa': transaction.sender_vpa,
            'receiver_vpa': transaction.receiver_vpa,
            'amount': float(transaction.amount),
            'remarks': transaction.remarks,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Make API request to NPCI gateway
            response = requests.post(
                f"{self.gateway_url}/process-transaction",
                headers=self._get_headers(),
                data=json.dumps(payload),
                timeout=self.timeout_seconds
            )
            
            # Handle response status
            if response.status_code == 401:
                raise GatewayAuthenticationError("Authentication failed with NPCI gateway")
            
            if response.status_code != 200:
                self.logger.error(f"NPCI gateway returned error: {response.status_code} - {response.text}")
                return {
                    'status': 'FAILED',
                    'error_code': f"HTTP_{response.status_code}",
                    'message': f"Gateway returned error: {response.text}"
                }
            
            # Parse and return response
            return response.json()
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout while connecting to NPCI gateway for transaction {transaction.transaction_id}")
            raise GatewayTimeoutError(f"NPCI gateway did not respond within {self.timeout_seconds} seconds")
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error with NPCI gateway: {str(e)}")
            raise GatewayConnectionError(f"Failed to connect to NPCI gateway: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Unexpected error processing transaction through NPCI gateway: {str(e)}")
            return {
                'status': 'FAILED',
                'error_code': 'INTERNAL_ERROR',
                'message': f"Internal error: {str(e)}"
            }
    
    def verify_transaction(self, transaction_id: UUID) -> Dict[str, Any]:
        """
        Verify a UPI transaction status with the NPCI gateway.
        
        Args:
            transaction_id: The ID of the transaction to verify
            
        Returns:
            Dictionary with the verification result
            
        Raises:
            GatewayConnectionError: If there's a connection error
            GatewayTimeoutError: If the gateway doesn't respond in time
            GatewayAuthenticationError: If authentication fails
        """
        self.logger.info(f"Verifying transaction {transaction_id} with NPCI gateway")
        
        # Use mock response if configured to do so
        if self.use_mock:
            self.logger.info("Using mock NPCI gateway verification response")
            return {
                'status': 'SUCCESS',
                'transaction_status': 'COMPLETED',
                'reference_id': f"NPCI-{transaction_id}",
                'timestamp': datetime.now().isoformat(),
                'message': 'Transaction was completed successfully'
            }
        
        try:
            # Make API request to NPCI gateway
            response = requests.get(
                f"{self.gateway_url}/verify-transaction/{transaction_id}",
                headers=self._get_headers(),
                timeout=self.timeout_seconds
            )
            
            # Handle response status
            if response.status_code == 401:
                raise GatewayAuthenticationError("Authentication failed with NPCI gateway")
            
            if response.status_code != 200:
                self.logger.error(f"NPCI gateway returned error: {response.status_code} - {response.text}")
                return {
                    'status': 'FAILED',
                    'error_code': f"HTTP_{response.status_code}",
                    'message': f"Gateway returned error: {response.text}"
                }
            
            # Parse and return response
            return response.json()
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout while verifying transaction {transaction_id} with NPCI gateway")
            raise GatewayTimeoutError(f"NPCI gateway did not respond within {self.timeout_seconds} seconds")
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error with NPCI gateway: {str(e)}")
            raise GatewayConnectionError(f"Failed to connect to NPCI gateway: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Unexpected error verifying transaction with NPCI gateway: {str(e)}")
            return {
                'status': 'FAILED',
                'error_code': 'INTERNAL_ERROR',
                'message': f"Internal error: {str(e)}"
            }
