"""
SQL Audit Log Service for RTGS transactions.
"""
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
import json

from ...application.interfaces.rtgs_audit_log_service_interface import RTGSAuditLogServiceInterface
from ...domain.entities.rtgs_transaction import RTGSTransaction

logger = logging.getLogger(__name__)


class SQLAuditLogService(RTGSAuditLogServiceInterface):
    """SQL implementation of audit log service."""
    
    def __init__(self, db_path: str):
        """
        Initialize the audit log service.
        
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
                CREATE TABLE IF NOT EXISTS rtgs_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT NOT NULL,
                    batch_id TEXT,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    user_id TEXT,
                    ip_address TEXT,
                    timestamp TEXT NOT NULL,
                    additional_details TEXT
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rtgs_audit_transaction_id ON rtgs_audit_logs(transaction_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rtgs_audit_event_type ON rtgs_audit_logs(event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rtgs_audit_timestamp ON rtgs_audit_logs(timestamp)')
            conn.commit()
    
    def log_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        transaction_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            event_data: Event data
            transaction_id: Optional transaction ID
            batch_id: Optional batch ID
            user_id: Optional user ID
            ip_address: Optional IP address
            additional_details: Optional additional details
            
        Returns:
            bool: True if logged successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO rtgs_audit_logs
                    (transaction_id, batch_id, event_type, event_data, user_id, ip_address, timestamp, additional_details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    transaction_id,
                    batch_id,
                    event_type,
                    json.dumps(event_data),
                    user_id,
                    ip_address,
                    datetime.utcnow().isoformat(),
                    json.dumps(additional_details) if additional_details else None
                ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to log RTGS audit event: {str(e)}")
            return False
    
    def log_transaction_created(self, transaction: RTGSTransaction, user_id: Optional[str] = None) -> bool:
        """
        Log transaction creation.
        
        Args:
            transaction: The transaction that was created
            user_id: Optional user ID
            
        Returns:
            bool: True if logged successfully
        """
        event_data = {
            "transaction_id": str(transaction.id),
            "transaction_reference": transaction.transaction_reference,
            "amount": transaction.payment_details.amount,
            "sender_account": transaction.payment_details.sender_account_number,
            "beneficiary_account": transaction.payment_details.beneficiary_account_number,
            "status": transaction.status.value
        }
        
        return self.log_event(
            event_type="TRANSACTION_CREATED",
            event_data=event_data,
            transaction_id=str(transaction.id),
            user_id=user_id
        )
    
    def log_transaction_updated(
        self, 
        transaction: RTGSTransaction, 
        old_status: str, 
        user_id: Optional[str] = None
    ) -> bool:
        """
        Log transaction update.
        
        Args:
            transaction: The transaction that was updated
            old_status: The previous status
            user_id: Optional user ID
            
        Returns:
            bool: True if logged successfully
        """
        event_data = {
            "transaction_id": str(transaction.id),
            "transaction_reference": transaction.transaction_reference,
            "old_status": old_status,
            "new_status": transaction.status.value,
            "utr_number": transaction.utr_number
        }
        
        return self.log_event(
            event_type="TRANSACTION_UPDATED",
            event_data=event_data,
            transaction_id=str(transaction.id),
            user_id=user_id
        )
    
    def log_batch_created(self, batch_id: str, batch_number: str, transaction_count: int, user_id: Optional[str] = None) -> bool:
        """
        Log batch creation.
        
        Args:
            batch_id: Batch ID
            batch_number: Batch number
            transaction_count: Number of transactions in the batch
            user_id: Optional user ID
            
        Returns:
            bool: True if logged successfully
        """
        event_data = {
            "batch_id": batch_id,
            "batch_number": batch_number,
            "transaction_count": transaction_count
        }
        
        return self.log_event(
            event_type="BATCH_CREATED",
            event_data=event_data,
            batch_id=batch_id,
            user_id=user_id
        )
    
    def log_batch_updated(self, batch_id: str, batch_number: str, old_status: str, new_status: str, user_id: Optional[str] = None) -> bool:
        """
        Log batch update.
        
        Args:
            batch_id: Batch ID
            batch_number: Batch number
            old_status: Old status
            new_status: New status
            user_id: Optional user ID
            
        Returns:
            bool: True if logged successfully
        """
        event_data = {
            "batch_id": batch_id,
            "batch_number": batch_number,
            "old_status": old_status,
            "new_status": new_status
        }
        
        return self.log_event(
            event_type="BATCH_UPDATED",
            event_data=event_data,
            batch_id=batch_id,
            user_id=user_id
        )
    
    def get_transaction_audit_trail(self, transaction_id: str) -> list:
        """
        Get audit trail for a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            list: Audit trail entries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM rtgs_audit_logs
                    WHERE transaction_id = ?
                    ORDER BY timestamp ASC
                ''', (transaction_id,))
                
                result = []
                for row in cursor.fetchall():
                    entry = dict(row)
                    # Parse JSON strings back to dictionaries
                    entry['event_data'] = json.loads(entry['event_data']) if entry['event_data'] else {}
                    entry['additional_details'] = json.loads(entry['additional_details']) if entry['additional_details'] else None
                    result.append(entry)
                
                return result
        except Exception as e:
            logger.error(f"Failed to get RTGS transaction audit trail: {str(e)}")
            return []
