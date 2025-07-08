"""
NEFT Batch Repository Interface.
This interface defines the contract for batch repositories.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ...domain.entities.neft_batch import NEFTBatch


class NEFTBatchRepositoryInterface(ABC):
    """Interface for NEFT batch repository."""
    
    @abstractmethod
    def get_by_id(self, batch_id: UUID) -> Optional[NEFTBatch]:
        """
        Get a batch by ID.
        
        Args:
            batch_id: The batch ID
            
        Returns:
            Optional[NEFTBatch]: The batch if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_batch_number(self, batch_number: str) -> Optional[NEFTBatch]:
        """
        Get a batch by batch number.
        
        Args:
            batch_number: The batch number
            
        Returns:
            Optional[NEFTBatch]: The batch if found, None otherwise
        """
        pass
    
    @abstractmethod
    def save(self, batch: NEFTBatch) -> NEFTBatch:
        """
        Save a batch.
        
        Args:
            batch: The batch to save
            
        Returns:
            NEFTBatch: The saved batch
        """
        pass
    
    @abstractmethod
    def update(self, batch: NEFTBatch) -> NEFTBatch:
        """
        Update a batch.
        
        Args:
            batch: The batch to update
            
        Returns:
            NEFTBatch: The updated batch
        """
        pass
    
    @abstractmethod
    def get_pending_batches(self) -> List[NEFTBatch]:
        """
        Get pending batches.
        
        Returns:
            List[NEFTBatch]: List of pending batches
        """
        pass
    
    @abstractmethod
    def get_batches_by_date(self, date_str: str) -> List[NEFTBatch]:
        """
        Get batches by date.
        
        Args:
            date_str: Date string in format YYYY-MM-DD
            
        Returns:
            List[NEFTBatch]: List of batches for the date
        """
        pass
