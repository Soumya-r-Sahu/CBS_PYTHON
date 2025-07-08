"""
SQLite implementation of the mobile transaction repository interface.
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import sqlite3

from ...domain.entities.mobile_transaction import MobileTransaction, TransactionStatus, TransactionType
from ...application.interfaces.mobile_transaction_repository_interface import MobileTransactionRepositoryInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class SQLMobileTransactionRepository(MobileTransactionRepositoryInterface):
    """SQLite implementation of the mobile transaction repository."""
    
    def __init__(self, db_connection):
        """
        Initialize the repository.
        
        Args:
            db_connection: SQLite database connection
        """
        self._connection = db_connection
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure the required tables exist in the database."""
        cursor = self._connection.cursor()
        
        # Create transactions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mobile_banking_transactions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            from_account TEXT NOT NULL,
            to_account TEXT NOT NULL,
            reference_number TEXT UNIQUE NOT NULL,
            remarks TEXT,
            status TEXT NOT NULL,
            risk_level INTEGER NOT NULL,
            initiation_time TEXT NOT NULL,
            verification_time TEXT,
            completion_time TEXT,
            ip_address TEXT,
            device_id TEXT,
            location TEXT,
            response_details TEXT,
            FOREIGN KEY (user_id) REFERENCES mobile_banking_users (id)
        )
        ''')
        
        # Create index on reference number
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS mobile_banking_transactions_reference_number
        ON mobile_banking_transactions (reference_number)
        ''')
        
        # Create index on user_id
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS mobile_banking_transactions_user_id
        ON mobile_banking_transactions (user_id)
        ''')
        
        self._connection.commit()
    
    def get_by_id(self, transaction_id: UUID) -> Optional[MobileTransaction]:
        """
        Get a transaction by its ID.
        
        Args:
            transaction_id: The ID of the transaction to get
            
        Returns:
            MobileTransaction if found, None otherwise
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM mobile_banking_transactions WHERE id = ?",
            (str(transaction_id),)
        )
        transaction_data = cursor.fetchone()
        
        if transaction_data is None:
            return None
        
        return self._transaction_from_row(transaction_data)
    
    def get_by_reference_number(self, reference_number: str) -> Optional[MobileTransaction]:
        """
        Get a transaction by its reference number.
        
        Args:
            reference_number: The reference number of the transaction to get
            
        Returns:
            MobileTransaction if found, None otherwise
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM mobile_banking_transactions WHERE reference_number = ?",
            (reference_number,)
        )
        transaction_data = cursor.fetchone()
        
        if transaction_data is None:
            return None
        
        return self._transaction_from_row(transaction_data)
    
    def get_by_user_id(self, user_id: UUID) -> List[MobileTransaction]:
        """
        Get all transactions for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of MobileTransaction objects
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM mobile_banking_transactions WHERE user_id = ? ORDER BY initiation_time DESC",
            (str(user_id),)
        )
        transaction_rows = cursor.fetchall()
        
        return [self._transaction_from_row(row) for row in transaction_rows]
    
    def get_by_user_id_and_date_range(
        self, 
        user_id: UUID, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[MobileTransaction]:
        """
        Get all transactions for a user within a date range.
        
        Args:
            user_id: The ID of the user
            start_date: The start date of the range
            end_date: The end date of the range
            
        Returns:
            List of MobileTransaction objects
        """
        cursor = self._connection.cursor()
        cursor.execute(
            """
            SELECT * FROM mobile_banking_transactions 
            WHERE user_id = ? 
            AND initiation_time >= ? 
            AND initiation_time <= ?
            ORDER BY initiation_time DESC
            """,
            (str(user_id), start_date.isoformat(), end_date.isoformat())
        )
        transaction_rows = cursor.fetchall()
        
        return [self._transaction_from_row(row) for row in transaction_rows]
    
    def save(self, transaction: MobileTransaction) -> MobileTransaction:
        """
        Save a transaction to the repository.
        
        Args:
            transaction: The transaction to save
            
        Returns:
            The saved transaction with any updates (e.g., ID assignment)
        """
        # Assign an ID if the transaction doesn't have one
        if transaction.id is None:
            transaction.id = uuid4()
        
        cursor = self._connection.cursor()
        
        # Convert location to JSON if present
        location_json = json.dumps(transaction.location) if transaction.location else None
        
        # Convert response_details to JSON if present
        response_details_json = json.dumps(transaction.response_details) if transaction.response_details else None
        
        # Insert the transaction
        cursor.execute('''
        INSERT INTO mobile_banking_transactions 
        (id, user_id, transaction_type, amount, from_account, to_account,
         reference_number, remarks, status, risk_level, initiation_time,
         verification_time, completion_time, ip_address, device_id, 
         location, response_details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(transaction.id),
            str(transaction.user_id),
            transaction.transaction_type.value,
            transaction.amount,
            transaction.from_account,
            transaction.to_account,
            transaction.reference_number,
            transaction.remarks,
            transaction.status.value,
            transaction.risk_level,
            transaction.initiation_time.isoformat() if transaction.initiation_time else None,
            transaction.verification_time.isoformat() if transaction.verification_time else None,
            transaction.completion_time.isoformat() if transaction.completion_time else None,
            transaction.ip_address,
            transaction.device_id,
            location_json,
            response_details_json
        ))
        
        self._connection.commit()
        return transaction
    
    def update(self, transaction: MobileTransaction) -> MobileTransaction:
        """
        Update an existing transaction.
        
        Args:
            transaction: The transaction to update
            
        Returns:
            The updated transaction
        """
        cursor = self._connection.cursor()
        
        # Convert location to JSON if present
        location_json = json.dumps(transaction.location) if transaction.location else None
        
        # Convert response_details to JSON if present
        response_details_json = json.dumps(transaction.response_details) if transaction.response_details else None
        
        # Update the transaction
        cursor.execute('''
        UPDATE mobile_banking_transactions SET
            user_id = ?,
            transaction_type = ?,
            amount = ?,
            from_account = ?,
            to_account = ?,
            reference_number = ?,
            remarks = ?,
            status = ?,
            risk_level = ?,
            initiation_time = ?,
            verification_time = ?,
            completion_time = ?,
            ip_address = ?,
            device_id = ?,
            location = ?,
            response_details = ?
        WHERE id = ?
        ''', (
            str(transaction.user_id),
            transaction.transaction_type.value,
            transaction.amount,
            transaction.from_account,
            transaction.to_account,
            transaction.reference_number,
            transaction.remarks,
            transaction.status.value,
            transaction.risk_level,
            transaction.initiation_time.isoformat() if transaction.initiation_time else None,
            transaction.verification_time.isoformat() if transaction.verification_time else None,
            transaction.completion_time.isoformat() if transaction.completion_time else None,
            transaction.ip_address,
            transaction.device_id,
            location_json,
            response_details_json,
            str(transaction.id)
        ))
        
        self._connection.commit()
        return transaction
    
    def _transaction_from_row(self, row: tuple) -> MobileTransaction:
        """
        Create a MobileTransaction from a database row.
        
        Args:
            row: Database row
            
        Returns:
            MobileTransaction object
        """
        # Extract columns based on order
        (id_str, user_id_str, transaction_type_str, amount, from_account, to_account,
         reference_number, remarks, status_str, risk_level, initiation_time_str,
         verification_time_str, completion_time_str, ip_address, device_id, 
         location_json, response_details_json) = row
        
        # Parse dates
        initiation_time = datetime.fromisoformat(initiation_time_str) if initiation_time_str else None
        verification_time = datetime.fromisoformat(verification_time_str) if verification_time_str else None
        completion_time = datetime.fromisoformat(completion_time_str) if completion_time_str else None
        
        # Parse JSON fields
        location = json.loads(location_json) if location_json else None
        response_details = json.loads(response_details_json) if response_details_json else {}
        
        # Parse enums
        transaction_type = TransactionType(transaction_type_str)
        status = TransactionStatus(status_str)
        
        # Create and return transaction
        return MobileTransaction(
            id=UUID(id_str),
            user_id=UUID(user_id_str),
            transaction_type=transaction_type,
            amount=amount,
            from_account=from_account,
            to_account=to_account,
            reference_number=reference_number,
            remarks=remarks,
            status=status,
            risk_level=risk_level,
            initiation_time=initiation_time,
            verification_time=verification_time,
            completion_time=completion_time,
            ip_address=ip_address,
            device_id=device_id,
            location=location,
            response_details=response_details
        )
