"""
SQL repository for RTGS batches.
"""
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import sqlite3
import json

from ...domain.entities.rtgs_batch import RTGSBatch, RTGSBatchStatus
from ...application.interfaces.rtgs_batch_repository_interface import RTGSBatchRepositoryInterface


class SQLRTGSBatchRepository(RTGSBatchRepositoryInterface):
    """SQL implementation of RTGS batch repository."""
    
    def __init__(self, db_path: str):
        """
        Initialize the repository.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self._create_tables_if_not_exist()
    
    def _create_tables_if_not_exist(self):
        """Create necessary tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rtgs_batches (
                    id TEXT PRIMARY KEY,
                    batch_number TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL,
                    transaction_count INTEGER DEFAULT 0,
                    total_amount REAL DEFAULT 0.0,
                    scheduled_time TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    processed_at TEXT,
                    completed_at TEXT,
                    transaction_ids TEXT
                )
            ''')
            conn.commit()
    
    def _batch_to_db_record(self, batch: RTGSBatch) -> tuple:
        """Convert a batch entity to a database record."""
        return (
            str(batch.id),
            batch.batch_number,
            batch.status.value,
            batch.transaction_count,
            batch.total_amount,
            batch.scheduled_time.isoformat(),
            batch.created_at.isoformat(),
            batch.updated_at.isoformat(),
            batch.processed_at.isoformat() if batch.processed_at else None,
            batch.completed_at.isoformat() if batch.completed_at else None,
            json.dumps([str(id) for id in batch.transaction_ids])
        )
    
    def _db_record_to_batch(self, record: tuple) -> RTGSBatch:
        """Convert a database record to a batch entity."""
        transaction_ids = json.loads(record[10]) if record[10] else []
        return RTGSBatch(
            id=UUID(record[0]),
            batch_number=record[1],
            status=RTGSBatchStatus(record[2]),
            transaction_count=record[3],
            total_amount=record[4],
            scheduled_time=datetime.fromisoformat(record[5]),
            created_at=datetime.fromisoformat(record[6]),
            updated_at=datetime.fromisoformat(record[7]),
            processed_at=datetime.fromisoformat(record[8]) if record[8] else None,
            completed_at=datetime.fromisoformat(record[9]) if record[9] else None,
            transaction_ids=[UUID(id) for id in transaction_ids]
        )
    
    def get_by_id(self, batch_id: UUID) -> Optional[RTGSBatch]:
        """
        Get a batch by ID.
        
        Args:
            batch_id: The batch ID
            
        Returns:
            Optional[RTGSBatch]: The batch if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM rtgs_batches WHERE id = ?', (str(batch_id),))
            record = cursor.fetchone()
            
            if record:
                return self._db_record_to_batch(tuple(record))
            return None
    
    def get_by_batch_number(self, batch_number: str) -> Optional[RTGSBatch]:
        """
        Get a batch by batch number.
        
        Args:
            batch_number: The batch number
            
        Returns:
            Optional[RTGSBatch]: The batch if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM rtgs_batches WHERE batch_number = ?', (batch_number,))
            record = cursor.fetchone()
            
            if record:
                return self._db_record_to_batch(tuple(record))
            return None
    
    def save(self, batch: RTGSBatch) -> RTGSBatch:
        """
        Save a batch.
        
        Args:
            batch: The batch to save
            
        Returns:
            RTGSBatch: The saved batch
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO rtgs_batches 
                (id, batch_number, status, transaction_count, total_amount, 
                scheduled_time, created_at, updated_at, processed_at, completed_at, transaction_ids)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', self._batch_to_db_record(batch))
            conn.commit()
            
        return batch
    
    def update(self, batch: RTGSBatch) -> RTGSBatch:
        """
        Update a batch.
        
        Args:
            batch: The batch to update
            
        Returns:
            RTGSBatch: The updated batch
        """
        # Update record timestamp
        batch.updated_at = datetime.utcnow()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE rtgs_batches SET
                batch_number = ?,
                status = ?,
                transaction_count = ?,
                total_amount = ?,
                scheduled_time = ?,
                created_at = ?,
                updated_at = ?,
                processed_at = ?,
                completed_at = ?,
                transaction_ids = ?
                WHERE id = ?
            ''', self._batch_to_db_record(batch)[1:] + (str(batch.id),))
            conn.commit()
            
        return batch
    
    def get_by_status(self, status: RTGSBatchStatus, limit: int = 100) -> List[RTGSBatch]:
        """
        Get batches by status.
        
        Args:
            status: The batch status
            limit: Maximum number of batches to return
            
        Returns:
            List[RTGSBatch]: List of batches
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM rtgs_batches WHERE status = ? ORDER BY created_at DESC LIMIT ?', 
                (status.value, limit)
            )
            records = cursor.fetchall()
            
            return [self._db_record_to_batch(tuple(record)) for record in records]
    
    def get_batches_by_date_range(self, start_date: datetime, end_date: datetime) -> List[RTGSBatch]:
        """
        Get batches by date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List[RTGSBatch]: List of batches
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM rtgs_batches WHERE created_at BETWEEN ? AND ? ORDER BY created_at DESC', 
                (start_date.isoformat(), end_date.isoformat())
            )
            records = cursor.fetchall()
            
            return [self._db_record_to_batch(tuple(record)) for record in records]
