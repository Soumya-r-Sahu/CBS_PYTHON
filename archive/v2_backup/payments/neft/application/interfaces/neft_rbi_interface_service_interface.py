"""
NEFT RBI Interface Service Interface.
This interface defines the contract for external RBI NEFT system integration.
"""
from abc import ABC, abstractmethod

from ...domain.entities.neft_transaction import NEFTTransaction
from ...domain.entities.neft_batch import NEFTBatch


class NEFTRbiInterfaceServiceInterface(ABC):
    """Interface for NEFT RBI interface service."""
    
    @abstractmethod
    def submit_transaction(self, transaction: NEFTTransaction) -> NEFTTransaction:
        """
        Submit a transaction to the RBI NEFT system.
        
        Args:
            transaction: The transaction to submit
            
        Returns:
            NEFTTransaction: The updated transaction with RBI response
        """
        pass
    
    @abstractmethod
    def submit_batch(self, batch: NEFTBatch, transactions: list[NEFTTransaction]) -> tuple[NEFTBatch, list[NEFTTransaction]]:
        """
        Submit a batch of transactions to the RBI NEFT system.
        
        Args:
            batch: The batch to submit
            transactions: The transactions in the batch
            
        Returns:
            tuple[NEFTBatch, list[NEFTTransaction]]: The updated batch and transactions
        """
        pass
    
    @abstractmethod
    def check_transaction_status(self, utr_number: str) -> dict:
        """
        Check the status of a transaction with the RBI NEFT system.
        
        Args:
            utr_number: UTR number assigned by RBI
            
        Returns:
            dict: Status response from RBI
        """
        pass
    
    @abstractmethod
    def check_batch_status(self, batch_number: str) -> dict:
        """
        Check the status of a batch with the RBI NEFT system.
        
        Args:
            batch_number: Batch number
            
        Returns:
            dict: Status response from RBI
        """
        pass
