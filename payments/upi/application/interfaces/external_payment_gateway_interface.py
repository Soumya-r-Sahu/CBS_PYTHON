"""
Interface for external payment gateway integrations.
"""
from typing import Dict, Any
from uuid import UUID

from ...domain.entities.upi_transaction import UpiTransaction


class ExternalPaymentGatewayInterface:
    """Interface for external payment gateway integrations."""
    
    def process_transaction(self, transaction: UpiTransaction) -> Dict[str, Any]:
        """
        Process a transaction through the external payment gateway.
        
        Args:
            transaction: The transaction to process
            
        Returns:
            Dictionary with the gateway response
        """
        raise NotImplementedError("External payment gateway must implement process_transaction")
    
    def verify_transaction(self, transaction_id: UUID) -> Dict[str, Any]:
        """
        Verify a transaction status with the external payment gateway.
        
        Args:
            transaction_id: The ID of the transaction to verify
            
        Returns:
            Dictionary with the verification result
        """
        raise NotImplementedError("External payment gateway must implement verify_transaction")
