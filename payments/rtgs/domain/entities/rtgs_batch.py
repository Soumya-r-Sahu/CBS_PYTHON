"""
RTGS Batch entity in the domain layer.
This entity represents a batch of RTGS transactions to be processed together.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4


class RTGSBatchStatus(str, Enum):
    """RTGS batch status enumeration."""
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    SENT_TO_RBI = "SENT_TO_RBI"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class RTGSBatch:
    """RTGS Batch entity that groups transactions for processing."""
    
    # Required fields
    id: UUID = field(default_factory=uuid4)
    batch_number: str = ""
    
    # System-populated fields
    status: RTGSBatchStatus = RTGSBatchStatus.CREATED
    transaction_count: int = 0
    total_amount: float = 0.0
    scheduled_time: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    transaction_ids: List[UUID] = field(default_factory=list)
    
    @classmethod
    def create(cls, batch_number: str, scheduled_time: datetime, transaction_ids: List[UUID] = None) -> 'RTGSBatch':
        """
        Create a new RTGS batch.
        
        Args:
            batch_number: Unique batch number
            scheduled_time: Scheduled processing time
            transaction_ids: List of transaction IDs in this batch
            
        Returns:
            RTGSBatch: The created batch
        """
        batch = cls(
            batch_number=batch_number,
            scheduled_time=scheduled_time,
            transaction_ids=transaction_ids or []
        )
        
        if transaction_ids:
            batch.transaction_count = len(transaction_ids)
        
        return batch
    
    def add_transaction(self, transaction_id: UUID, transaction_amount: float) -> None:
        """
        Add a transaction to the batch.
        
        Args:
            transaction_id: ID of the transaction
            transaction_amount: Amount of the transaction
        """
        if transaction_id not in self.transaction_ids:
            self.transaction_ids.append(transaction_id)
            self.transaction_count += 1
            self.total_amount += transaction_amount
            self.updated_at = datetime.utcnow()
    
    def remove_transaction(self, transaction_id: UUID, transaction_amount: float) -> None:
        """
        Remove a transaction from the batch.
        
        Args:
            transaction_id: ID of the transaction
            transaction_amount: Amount of the transaction
        """
        if transaction_id in self.transaction_ids:
            self.transaction_ids.remove(transaction_id)
            self.transaction_count -= 1
            self.total_amount -= transaction_amount
            self.updated_at = datetime.utcnow()
    
    def update_status(self, status: RTGSBatchStatus) -> None:
        """
        Update the batch status.
        
        Args:
            status: New status
        """
        self.status = status
        self.updated_at = datetime.utcnow()
        
        if status == RTGSBatchStatus.COMPLETED:
            self.completed_at = datetime.utcnow()
        elif status == RTGSBatchStatus.PROCESSING:
            self.processed_at = datetime.utcnow()
