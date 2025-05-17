"""
RTGS Batch Repository Interface.
This interface defines the contract for batch repositories.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ...domain.entities.rtgs_batch import RTGSBatch


class RTGSBatchRepositoryInterface(ABC):
    """Interface for RTGS batch repository."""
    
    @abstractmethod
    def get_by_id(self, batch_id: UUID) -> Optional[RTGSBatch]:
        """
        Get a batch by ID.
        
        Args:
            batch_id: The batch ID
            
        Returns:
            Optional[RTGSBatch]: The batch if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_batch_number(self, batch_number: str) -> Optional[RTGSBatch]:
        """
        Get a batch by batch number.
        
        Args:
            batch_number: The batch number
            
        Returns:
            Optional[RTGSBatch]: The batch if found, None otherwise
        """
        pass
    
    @abstractmethod
    def save(self, batch: RTGSBatch) -> RTGSBatch:
        """
        Save a batch.
        
        Args:
            batch: The batch to save
            
        Returns:
            RTGSBatch: The saved batch
        """
        pass
    
    @abstractmethod
    def update(self, batch: RTGSBatch) -> RTGSBatch:
        """
        Update a batch.
        
        Args:
            batch: The batch to update
            
        Returns:
            RTGSBatch: The updated batch
        """
        pass
    
    @abstractmethod
    def get_by_status(self, status: str, limit: int = 10) -> List[RTGSBatch]:
        """
        Get batches by status.
        
        Args:
            status: The batch status
            limit: Maximum number of batches to return
            
        Returns:
            List[RTGSBatch]: List of batches
        """
        pass
    
    @abstractmethod
    def get_by_date_range(self, start_date: str, end_date: str, limit: int = 100) -> List[RTGSBatch]:
        """
        Get batches by date range.
        
        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            limit: Maximum number of batches to return
            
        Returns:
            List[RTGSBatch]: List of batches
        """
        pass
