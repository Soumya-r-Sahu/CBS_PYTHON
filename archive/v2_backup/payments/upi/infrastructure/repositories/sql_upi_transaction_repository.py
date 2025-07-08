"""
SQL implementation of UPI transaction repository.
"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

import sqlite3

from ...domain.entities.upi_transaction import UpiTransaction, UpiTransactionStatus
from ...application.interfaces.upi_transaction_repository_interface import UpiTransactionRepositoryInterface


class SqlUpiTransactionRepository(UpiTransactionRepositoryInterface):
    """SQL implementation of UPI transaction repository."""
    
    def __init__(self, db_connection_string: str):
        """
        Initialize with database connection string.
        
        Args:
            db_connection_string: Connection string for the database
        """
        self.db_connection_string = db_connection_string
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self.db_connection_string)
    
    def _transaction_from_row(self, row: Dict[str, Any]) -> UpiTransaction:
        """Convert a database row to a UpiTransaction entity."""
        return UpiTransaction(
            transaction_id=UUID(row['transaction_id']),
            sender_vpa=row['sender_vpa'],
            receiver_vpa=row['receiver_vpa'],
            amount=float(row['amount']),
            transaction_date=datetime.fromisoformat(row['transaction_date']),
            status=UpiTransactionStatus(row['status']),
            remarks=row['remarks'],
            reference_id=row['reference_id'],
            failure_reason=row['failure_reason']
        )
    
    def save(self, transaction: UpiTransaction) -> None:
        """
        Save a UPI transaction to the repository.
        
        Args:
            transaction: The UPI transaction to save
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS upi_transactions (
                    transaction_id TEXT PRIMARY KEY,
                    sender_vpa TEXT NOT NULL,
                    receiver_vpa TEXT NOT NULL,
                    amount REAL NOT NULL,
                    transaction_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    remarks TEXT,
                    reference_id TEXT,
                    failure_reason TEXT
                )
            ''')
            
            # Insert the transaction
            cursor.execute('''
                INSERT INTO upi_transactions 
                (transaction_id, sender_vpa, receiver_vpa, amount, 
                transaction_date, status, remarks, reference_id, failure_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(transaction.transaction_id),
                transaction.sender_vpa,
                transaction.receiver_vpa,
                transaction.amount,
                transaction.transaction_date.isoformat(),
                transaction.status.value,
                transaction.remarks,
                transaction.reference_id,
                transaction.failure_reason
            ))
            
            conn.commit()
        finally:
            conn.close()
    
    def get_by_id(self, transaction_id: UUID) -> Optional[UpiTransaction]:
        """
        Get a UPI transaction by ID.
        
        Args:
            transaction_id: The ID of the transaction to retrieve
            
        Returns:
            UpiTransaction if found, None otherwise
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.row_factory = sqlite3.Row
            
            cursor.execute('''
                SELECT * FROM upi_transactions
                WHERE transaction_id = ?
            ''', (str(transaction_id),))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return self._transaction_from_row(row)
        finally:
            conn.close()
    
    def update(self, transaction: UpiTransaction) -> None:
        """
        Update an existing UPI transaction.
        
        Args:
            transaction: The UPI transaction to update
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE upi_transactions
                SET status = ?, reference_id = ?, failure_reason = ?
                WHERE transaction_id = ?
            ''', (
                transaction.status.value,
                transaction.reference_id,
                transaction.failure_reason,
                str(transaction.transaction_id)
            ))
            
            conn.commit()
        finally:
            conn.close()
    
    def get_transactions_by_vpa(self, vpa: str, 
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               status: Optional[UpiTransactionStatus] = None) -> List[UpiTransaction]:
        """
        Get transactions by VPA with optional filters.
        
        Args:
            vpa: VPA to search for (as sender or receiver)
            start_date: Optional start date filter
            end_date: Optional end date filter
            status: Optional status filter
            
        Returns:
            List of UPI transactions matching the criteria
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.row_factory = sqlite3.Row
            
            query = '''
                SELECT * FROM upi_transactions
                WHERE (sender_vpa = ? OR receiver_vpa = ?)
            '''
            params = [vpa, vpa]
            
            if start_date:
                query += ' AND transaction_date >= ?'
                params.append(start_date.isoformat())
            
            if end_date:
                query += ' AND transaction_date <= ?'
                params.append(end_date.isoformat())
            
            if status:
                query += ' AND status = ?'
                params.append(status.value)
            
            query += ' ORDER BY transaction_date DESC'
            
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            return [self._transaction_from_row(row) for row in rows]
        finally:
            conn.close()
    
    def get_daily_transaction_total(self, vpa: str, transaction_date: date) -> float:
        """
        Get the total amount of transactions for a VPA on a specific date.
        
        Args:
            vpa: VPA to calculate total for
            transaction_date: Date to calculate total for
            
        Returns:
            Total amount of transactions
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Convert date to datetime range
            start_date = datetime.combine(transaction_date, datetime.min.time())
            end_date = datetime.combine(transaction_date, datetime.max.time())
            
            cursor.execute('''
                SELECT SUM(amount) as total FROM upi_transactions
                WHERE sender_vpa = ?
                AND transaction_date BETWEEN ? AND ?
                AND status IN (?, ?, ?)
            ''', (
                vpa,
                start_date.isoformat(),
                end_date.isoformat(),
                UpiTransactionStatus.INITIATED.value,
                UpiTransactionStatus.PENDING.value,
                UpiTransactionStatus.COMPLETED.value
            ))
            
            result = cursor.fetchone()
            return float(result[0]) if result[0] else 0.0
        finally:
            conn.close()
