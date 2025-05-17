"""
SQL NEFT Batch Repository.
Implementation of the NEFTBatchRepositoryInterface using SQL database.
"""
import logging
from typing import Optional, List
from uuid import UUID
import json
from datetime import datetime

from ...domain.entities.neft_batch import NEFTBatch, NEFTBatchStatus
from ...application.interfaces.neft_batch_repository_interface import NEFTBatchRepositoryInterface


class SQLNEFTBatchRepository(NEFTBatchRepositoryInterface):
    """SQL implementation of NEFT batch repository."""
    
    def __init__(self, db_connection):
        """
        Initialize the repository.
        
        Args:
            db_connection: Database connection
        """
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
    
    def get_by_id(self, batch_id: UUID) -> Optional[NEFTBatch]:
        """
        Get a batch by ID.
        
        Args:
            batch_id: The batch ID
            
        Returns:
            Optional[NEFTBatch]: The batch if found, None otherwise
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT
                    id, batch_number, batch_time, total_transactions,
                    total_amount, completed_transactions, failed_transactions,
                    status, created_at, updated_at, submitted_at, completed_at,
                    transaction_ids, metadata
                FROM neft_batches
                WHERE id = ?
                """,
                (str(batch_id),)
            )
            
            row = cursor.fetchone()
            if not row:
                return None
                
            # Extract data
            (
                id_str, batch_number, batch_time_str, total_transactions,
                total_amount, completed_transactions, failed_transactions,
                status_str, created_at_str, updated_at_str, submitted_at_str, completed_at_str,
                transaction_ids_json, metadata_json
            ) = row
            
            # Convert strings to appropriate types
            id = UUID(id_str)
            batch_time = datetime.fromisoformat(batch_time_str)
            status = NEFTBatchStatus(status_str)
            created_at = datetime.fromisoformat(created_at_str)
            updated_at = datetime.fromisoformat(updated_at_str)
            submitted_at = datetime.fromisoformat(submitted_at_str) if submitted_at_str else None
            completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else None
            transaction_ids = [UUID(tx_id) for tx_id in json.loads(transaction_ids_json)] if transaction_ids_json else []
            metadata = json.loads(metadata_json) if metadata_json else {}
            
            # Create batch object
            batch = NEFTBatch(
                id=id,
                batch_number=batch_number,
                batch_time=batch_time,
                total_transactions=total_transactions,
                total_amount=total_amount,
                completed_transactions=completed_transactions,
                failed_transactions=failed_transactions,
                status=status,
                created_at=created_at,
                updated_at=updated_at,
                submitted_at=submitted_at,
                completed_at=completed_at,
                transaction_ids=transaction_ids,
                metadata=metadata
            )
            
            return batch
            
        except Exception as e:
            self.logger.error(f"Error getting NEFT batch by ID: {e}")
            return None
    
    def get_by_batch_number(self, batch_number: str) -> Optional[NEFTBatch]:
        """
        Get a batch by batch number.
        
        Args:
            batch_number: The batch number
            
        Returns:
            Optional[NEFTBatch]: The batch if found, None otherwise
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT
                    id, batch_number, batch_time, total_transactions,
                    total_amount, completed_transactions, failed_transactions,
                    status, created_at, updated_at, submitted_at, completed_at,
                    transaction_ids, metadata
                FROM neft_batches
                WHERE batch_number = ?
                """,
                (batch_number,)
            )
            
            row = cursor.fetchone()
            if not row:
                return None
                
            (
                id_str, batch_number, batch_time_str, total_transactions,
                total_amount, completed_transactions, failed_transactions,
                status_str, created_at_str, updated_at_str, submitted_at_str, completed_at_str,
                transaction_ids_json, metadata_json
            ) = row

            id = UUID(id_str)
            batch_time = datetime.fromisoformat(batch_time_str)
            status = NEFTBatchStatus(status_str)
            created_at = datetime.fromisoformat(created_at_str)
            updated_at = datetime.fromisoformat(updated_at_str)
            submitted_at = datetime.fromisoformat(submitted_at_str) if submitted_at_str else None
            completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else None
            transaction_ids = [UUID(tx_id) for tx_id in json.loads(transaction_ids_json)] if transaction_ids_json else []
            metadata = json.loads(metadata_json) if metadata_json else {}

            batch = NEFTBatch(
                id=id,
                batch_number=batch_number,
                batch_time=batch_time,
                total_transactions=total_transactions,
                total_amount=total_amount,
                completed_transactions=completed_transactions,
                failed_transactions=failed_transactions,
                status=status,
                created_at=created_at,
                updated_at=updated_at,
                submitted_at=submitted_at,
                completed_at=completed_at,
                transaction_ids=transaction_ids,
                metadata=metadata
            )
            
            return batch
            
        except Exception as e:
            self.logger.error(f"Error getting NEFT batch by batch number: {e}")
            return None
    
    def save(self, batch: NEFTBatch) -> NEFTBatch:
        """
        Save a batch.
        
        Args:
            batch: The batch to save
            
        Returns:
            NEFTBatch: The saved batch
        """
        try:
            cursor = self.db.cursor()
            
            # Serialize transaction_ids
            transaction_ids_json = json.dumps([str(tx_id) for tx_id in batch.transaction_ids])
            
            # Serialize metadata
            metadata_json = json.dumps(batch.metadata) if batch.metadata else None
            
            # Insert the batch
            cursor.execute(
                """
                INSERT INTO neft_batches (
                    id, batch_number, batch_time, total_transactions,
                    total_amount, completed_transactions, failed_transactions,
                    status, created_at, updated_at, submitted_at, completed_at,
                    transaction_ids, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(batch.id),
                    batch.batch_number,
                    batch.batch_time.isoformat(),
                    batch.total_transactions,
                    batch.total_amount,
                    batch.completed_transactions,
                    batch.failed_transactions,
                    batch.status.value,
                    batch.created_at.isoformat(),
                    batch.updated_at.isoformat(),
                    batch.submitted_at.isoformat() if batch.submitted_at else None,
                    batch.completed_at.isoformat() if batch.completed_at else None,
                    transaction_ids_json,
                    metadata_json
                )
            )
            
            self.db.commit()
            return batch
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error saving NEFT batch: {e}")
            raise
    
    def update(self, batch: NEFTBatch) -> NEFTBatch:
        """
        Update a batch.
        
        Args:
            batch: The batch to update
            
        Returns:
            NEFTBatch: The updated batch
        """
        try:
            cursor = self.db.cursor()
            
            # Serialize transaction_ids
            transaction_ids_json = json.dumps([str(tx_id) for tx_id in batch.transaction_ids])
            
            # Serialize metadata
            metadata_json = json.dumps(batch.metadata) if batch.metadata else None
            
            # Update the batch
            cursor.execute(
                """
                UPDATE neft_batches SET
                    batch_number = ?,
                    batch_time = ?,
                    total_transactions = ?,
                    total_amount = ?,
                    completed_transactions = ?,
                    failed_transactions = ?,
                    status = ?,
                    updated_at = ?,
                    submitted_at = ?,
                    completed_at = ?,
                    transaction_ids = ?,
                    metadata = ?
                WHERE id = ?
                """,
                (
                    batch.batch_number,
                    batch.batch_time.isoformat(),
                    batch.total_transactions,
                    batch.total_amount,
                    batch.completed_transactions,
                    batch.failed_transactions,
                    batch.status.value,
                    batch.updated_at.isoformat(),
                    batch.submitted_at.isoformat() if batch.submitted_at else None,
                    batch.completed_at.isoformat() if batch.completed_at else None,
                    transaction_ids_json,
                    metadata_json,
                    str(batch.id)
                )
            )
            
            self.db.commit()
            return batch
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error updating NEFT batch: {e}")
            raise
    
    def get_pending_batches(self) -> List[NEFTBatch]:
        """
        Get pending batches.
        
        Returns:
            List[NEFTBatch]: List of pending batches
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT
                    id, batch_number, batch_time, total_transactions,
                    total_amount, completed_transactions, failed_transactions,
                    status, created_at, updated_at, submitted_at, completed_at,
                    transaction_ids, metadata
                FROM neft_batches
                WHERE status = ?
                ORDER BY batch_time ASC
                """,
                (NEFTBatchStatus.PENDING.value,)
            )
            
            batches = []
            for row in cursor.fetchall():
                (
                    id_str, batch_number, batch_time_str, total_transactions,
                    total_amount, completed_transactions, failed_transactions,
                    status_str, created_at_str, updated_at_str, submitted_at_str, completed_at_str,
                    transaction_ids_json, metadata_json
                ) = row

                id = UUID(id_str)
                batch_time = datetime.fromisoformat(batch_time_str)
                status = NEFTBatchStatus(status_str)
                created_at = datetime.fromisoformat(created_at_str)
                updated_at = datetime.fromisoformat(updated_at_str)
                submitted_at = datetime.fromisoformat(submitted_at_str) if submitted_at_str else None
                completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else None
                transaction_ids = [UUID(tx_id) for tx_id in json.loads(transaction_ids_json)] if transaction_ids_json else []
                metadata = json.loads(metadata_json) if metadata_json else {}

                batch = NEFTBatch(
                    id=id,
                    batch_number=batch_number,
                    batch_time=batch_time,
                    total_transactions=total_transactions,
                    total_amount=total_amount,
                    completed_transactions=completed_transactions,
                    failed_transactions=failed_transactions,
                    status=status,
                    created_at=created_at,
                    updated_at=updated_at,
                    submitted_at=submitted_at,
                    completed_at=completed_at,
                    transaction_ids=transaction_ids,
                    metadata=metadata
                )
                batches.append(batch)
            
            return batches
            
        except Exception as e:
            self.logger.error(f"Error getting pending NEFT batches: {e}")
            return []
    
    def get_batches_by_date(self, date_str: str) -> List[NEFTBatch]:
        """
        Get batches by date.
        
        Args:
            date_str: Date string in format YYYY-MM-DD
            
        Returns:
            List[NEFTBatch]: List of batches for the date
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT
                    id, batch_number, batch_time, total_transactions,
                    total_amount, completed_transactions, failed_transactions,
                    status, created_at, updated_at, submitted_at, completed_at,
                    transaction_ids, metadata
                FROM neft_batches
                WHERE DATE(batch_time) = ?
                ORDER BY batch_time ASC
                """,
                (date_str,)
            )
            
            batches = []
            for row in cursor.fetchall():
                (
                    id_str, batch_number, batch_time_str, total_transactions,
                    total_amount, completed_transactions, failed_transactions,
                    status_str, created_at_str, updated_at_str, submitted_at_str, completed_at_str,
                    transaction_ids_json, metadata_json
                ) = row

                id = UUID(id_str)
                batch_time = datetime.fromisoformat(batch_time_str)
                status = NEFTBatchStatus(status_str)
                created_at = datetime.fromisoformat(created_at_str)
                updated_at = datetime.fromisoformat(updated_at_str)
                submitted_at = datetime.fromisoformat(submitted_at_str) if submitted_at_str else None
                completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else None
                transaction_ids = [UUID(tx_id) for tx_id in json.loads(transaction_ids_json)] if transaction_ids_json else []
                metadata = json.loads(metadata_json) if metadata_json else {}

                batch = NEFTBatch(
                    id=id,
                    batch_number=batch_number,
                    batch_time=batch_time,
                    total_transactions=total_transactions,
                    total_amount=total_amount,
                    completed_transactions=completed_transactions,
                    failed_transactions=failed_transactions,
                    status=status,
                    created_at=created_at,
                    updated_at=updated_at,
                    submitted_at=submitted_at,
                    completed_at=completed_at,
                    transaction_ids=transaction_ids,
                    metadata=metadata
                )
                batches.append(batch)
            
            return batches
            
        except Exception as e:
            self.logger.error(f"Error getting NEFT batches by date: {e}")
            return []
