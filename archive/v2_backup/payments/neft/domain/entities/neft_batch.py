"""
NEFT Batch entity in the domain layer.
This entity represents a batch of NEFT transactions processed together.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4


class NEFTBatchStatus(str, Enum):
    """NEFT batch status enumeration."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUBMITTED = "SUBMITTED"  # Submitted to RBI
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"


@dataclass
class NEFTBatch:
    """NEFT Batch entity that encapsulates a group of NEFT transactions."""
    
    # Required fields
    id: UUID = field(default_factory=uuid4)
    batch_number: str
    batch_time: datetime
    
    # System-populated fields
    total_transactions: int = 0
    total_amount: float = 0.0
    completed_transactions: int = 0
    failed_transactions: int = 0
    status: NEFTBatchStatus = NEFTBatchStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    transaction_ids: List[UUID] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(cls, batch_number: str, batch_time: datetime) -> 'NEFTBatch':
        """
        Factory method to create a new NEFT batch.
        
        Args:
            batch_number: The batch number
            batch_time: The scheduled batch time
            
        Returns:
            A new NEFTBatch
        """
        return cls(
            batch_number=batch_number,
            batch_time=batch_time
        )
    
    def add_transaction(self, transaction_id: UUID, amount: float):
        """
        Add a transaction to the batch.
        
        Args:
            transaction_id: The transaction ID
            amount: The transaction amount
        """
        if transaction_id not in self.transaction_ids:
            self.transaction_ids.append(transaction_id)
            self.total_transactions += 1
            self.total_amount += amount
            self.updated_at = datetime.utcnow()
    
    def update_status(self, new_status: NEFTBatchStatus):
        """
        Update batch status and related timestamps.
        
        Args:
            new_status: The new status
        """
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if new_status == NEFTBatchStatus.SUBMITTED:
            self.submitted_at = datetime.utcnow()
        elif new_status in [NEFTBatchStatus.COMPLETED, NEFTBatchStatus.FAILED, NEFTBatchStatus.PARTIALLY_COMPLETED]:
            self.completed_at = datetime.utcnow()
    
    def record_transaction_result(self, success: bool):
        """
        Record a transaction result.
        
        Args:
            success: Whether the transaction was successful
        """
        if success:
            self.completed_transactions += 1
        else:
            self.failed_transactions += 1
            
        self.updated_at = datetime.utcnow()
        
        # Update batch status if all transactions are processed
        if self.completed_transactions + self.failed_transactions == self.total_transactions:
            if self.failed_transactions == 0:
                self.update_status(NEFTBatchStatus.COMPLETED)
            elif self.completed_transactions == 0:
                self.update_status(NEFTBatchStatus.FAILED)
            else:
                self.update_status(NEFTBatchStatus.PARTIALLY_COMPLETED)
    
    def is_complete(self) -> bool:
        """
        Check if the batch processing is complete.
        
        Returns:
            True if complete
        """
        return self.completed_transactions + self.failed_transactions == self.total_transactions
    
    def is_successful(self) -> bool:
        """
        Check if the batch completed successfully (all transactions succeeded).
        
        Returns:
            True if successful
        """
        return self.status == NEFTBatchStatus.COMPLETED
