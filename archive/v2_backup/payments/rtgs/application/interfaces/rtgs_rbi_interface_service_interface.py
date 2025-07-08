"""
RTGS RBI Interface Service Interface.
This interface defines the contract for services that interact with the RBI's RTGS system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from uuid import UUID

from ...domain.entities.rtgs_transaction import RTGSTransaction
from ...domain.entities.rtgs_batch import RTGSBatch


class RTGSRBIInterfaceServiceInterface(ABC):
    """Interface for RTGS RBI interface service."""
    
    @abstractmethod
    def send_transaction(self, transaction: RTGSTransaction) -> Dict[str, Any]:
        """
        Send a transaction to the RBI RTGS system.
        
        Args:
            transaction: The transaction to send
            
        Returns:
            Dict[str, Any]: Response from the RBI system
        """
        pass
    
    @abstractmethod
    def send_batch(self, batch: RTGSBatch, transactions: List[RTGSTransaction]) -> Dict[str, Any]:
        """
        Send a batch of transactions to the RBI RTGS system.
        
        Args:
            batch: The batch to send
            transactions: List of transactions in the batch
            
        Returns:
            Dict[str, Any]: Response from the RBI system
        """
        pass
    
    @abstractmethod
    def check_transaction_status(self, utr_number: str) -> Dict[str, Any]:
        """
        Check the status of a transaction in the RBI RTGS system.
        
        Args:
            utr_number: Unique Transaction Reference number
            
        Returns:
            Dict[str, Any]: Status information
        """
        pass
    
    @abstractmethod
    def check_batch_status(self, batch_number: str) -> Dict[str, Any]:
        """
        Check the status of a batch in the RBI RTGS system.
        
        Args:
            batch_number: The batch number
            
        Returns:
            Dict[str, Any]: Status information
        """
        pass
    
    @abstractmethod
    def cancel_transaction(self, utr_number: str) -> Dict[str, Any]:
        """
        Request cancellation of a transaction in the RBI RTGS system.
        
        Args:
            utr_number: Unique Transaction Reference number
            
        Returns:
            Dict[str, Any]: Response from the RBI system
        """
        pass
