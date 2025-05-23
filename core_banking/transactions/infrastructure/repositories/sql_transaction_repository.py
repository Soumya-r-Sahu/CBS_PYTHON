"""
SQL Transaction Repository

This module implements the transaction repository interface using SQL database,
leveraging centralized utilities for error handling and data manipulation.
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...domain.entities.transaction import Transaction, TransactionStatus, TransactionType
from ...application.interfaces.transaction_repository import TransactionRepositoryInterface
from core_banking.utils.core_banking_utils import DatabaseException


class SqlTransactionRepository(TransactionRepositoryInterface):
    """SQL implementation of transaction repository"""
    
    def __init__(self, db_connection):
        """
        Initialize repository with database connection
        
        Args:
            db_connection: Database connection object
        """
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
    
    def create(self, transaction: Transaction) -> Transaction:
        """
        Create a new transaction
        
        Args:
            transaction: Transaction to create
            
        Returns:
            Created transaction
            
        Raises:
            DatabaseException: If there was an error creating the transaction
        """
        try:
            cursor = self.db.cursor()
            
            query = """
                INSERT INTO transactions (
                    id, transaction_id, account_id, amount, transaction_type,
                    description, status, timestamp, reference_number,
                    source_account_id, destination_account_id, processed_by,
                    processing_date, reversal_reference, currency
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
            """
            
            values = (
                str(transaction.id),
                transaction.transaction_id,
                str(transaction.account_id),
                float(transaction.amount),
                transaction.transaction_type.value,
                transaction.description,
                transaction.status.value,
                transaction.timestamp,
                transaction.reference_number,
                str(transaction.source_account_id) if transaction.source_account_id else None,
                str(transaction.destination_account_id) if transaction.destination_account_id else None,
                transaction.processed_by,
                transaction.processing_date,
                transaction.reversal_reference,
                transaction.currency
            )
            
            cursor.execute(query, values)
            self.db.commit()
            
            self.logger.info(f"Created transaction {transaction.transaction_id}")
            return transaction
            
        except Exception as e:
            self.db.rollback()
            error_msg = f"Failed to create transaction: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseException(error_msg, "DB_INSERT_ERROR")
    
    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """
        Get a transaction by ID
        
        Args:
            transaction_id: ID of the transaction
            
        Returns:
            Transaction if found, None otherwise
            
        Raises:
            DatabaseException: If there was an error retrieving the transaction
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            
            query = """
                SELECT * FROM transactions
                WHERE id = %s
            """
            
            cursor.execute(query, (str(transaction_id),))
            record = cursor.fetchone()
            
            if not record:
                return None
            
            return self._map_to_transaction(record)
            
        except Exception as e:
            error_msg = f"Failed to get transaction by ID: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseException(error_msg, "DB_SELECT_ERROR")
    
    def get_by_reference_number(self, reference_number: str) -> Optional[Transaction]:
        """
        Get a transaction by reference number
        
        Args:
            reference_number: Reference number of the transaction
            
        Returns:
            Transaction if found, None otherwise
            
        Raises:
            DatabaseException: If there was an error retrieving the transaction
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            
            query = """
                SELECT * FROM transactions
                WHERE reference_number = %s
            """
            
            cursor.execute(query, (reference_number,))
            record = cursor.fetchone()
            
            if not record:
                return None
            
            return self._map_to_transaction(record)
            
        except Exception as e:
            error_msg = f"Failed to get transaction by reference number: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseException(error_msg, "DB_SELECT_ERROR")
    
    def update(self, transaction: Transaction) -> Transaction:
        """
        Update an existing transaction
        
        Args:
            transaction: Transaction to update
            
        Returns:
            Updated transaction
            
        Raises:
            DatabaseException: If there was an error updating the transaction
        """
        try:
            cursor = self.db.cursor()
            
            query = """
                UPDATE transactions SET
                    transaction_id = %s,
                    account_id = %s,
                    amount = %s,
                    transaction_type = %s,
                    description = %s,
                    status = %s,
                    timestamp = %s,
                    reference_number = %s,
                    source_account_id = %s,
                    destination_account_id = %s,
                    processed_by = %s,
                    processing_date = %s,
                    reversal_reference = %s,
                    currency = %s
                WHERE id = %s
            """
            
            values = (
                transaction.transaction_id,
                str(transaction.account_id),
                float(transaction.amount),
                transaction.transaction_type.value,
                transaction.description,
                transaction.status.value,
                transaction.timestamp,
                transaction.reference_number,
                str(transaction.source_account_id) if transaction.source_account_id else None,
                str(transaction.destination_account_id) if transaction.destination_account_id else None,
                transaction.processed_by,
                transaction.processing_date,
                transaction.reversal_reference,
                transaction.currency,
                str(transaction.id)
            )
            
            cursor.execute(query, values)
            self.db.commit()
            
            self.logger.info(f"Updated transaction {transaction.transaction_id}")
            return transaction
            
        except Exception as e:
            self.db.rollback()
            error_msg = f"Failed to update transaction: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseException(error_msg, "DB_UPDATE_ERROR")
    
    def get_account_transactions(
        self, 
        account_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """
        Get transactions for a specific account
        
        Args:
            account_id: ID of the account
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            transaction_type: Filter by transaction type
            status: Filter by transaction status
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of transactions
            
        Raises:
            DatabaseException: If there was an error retrieving the transactions
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            
            # Build query with filters
            query = """
                SELECT * FROM transactions
                WHERE (account_id = %s OR source_account_id = %s OR destination_account_id = %s)
            """
            params = [str(account_id), str(account_id), str(account_id)]
            
            if start_date:
                query += " AND DATE(timestamp) >= %s"
                params.append(start_date)
                
            if end_date:
                query += " AND DATE(timestamp) <= %s"
                params.append(end_date)
                
            if transaction_type:
                query += " AND transaction_type = %s"
                params.append(transaction_type.value)
                
            if status:
                query += " AND status = %s"
                params.append(status.value)
                
            query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            records = cursor.fetchall()
            
            return [self._map_to_transaction(record) for record in records]
            
        except Exception as e:
            error_msg = f"Failed to get account transactions: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseException(error_msg, "DB_SELECT_ERROR")
    
    def get_transactions_by_date_range(
        self,
        start_date: date,
        end_date: date,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """
        Get all transactions within a date range
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of transactions
            
        Raises:
            DatabaseException: If there was an error retrieving the transactions
        """
        try:
            cursor = self.db.cursor(dictionary=True)
            
            query = """
                SELECT * FROM transactions
                WHERE DATE(timestamp) BETWEEN %s AND %s
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """
            
            params = [start_date, end_date, limit, offset]
            cursor.execute(query, params)
            records = cursor.fetchall()
            
            return [self._map_to_transaction(record) for record in records]
            
        except Exception as e:
            error_msg = f"Failed to get transactions by date range: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseException(error_msg, "DB_SELECT_ERROR")
    
    def _map_to_transaction(self, record: Dict[str, Any]) -> Transaction:
        """
        Map database record to Transaction entity
        
        Args:
            record: Database record
            
        Returns:
            Transaction entity
        """
        return Transaction(
            id=UUID(record['id']),
            transaction_id=record['transaction_id'],
            account_id=UUID(record['account_id']),
            amount=Decimal(str(record['amount'])),
            transaction_type=TransactionType(record['transaction_type']),
            description=record['description'],
            status=TransactionStatus(record['status']),
            timestamp=record['timestamp'],
            reference_number=record['reference_number'],
            source_account_id=UUID(record['source_account_id']) if record['source_account_id'] else None,
            destination_account_id=UUID(record['destination_account_id']) if record['destination_account_id'] else None,
            processed_by=record['processed_by'],
            processing_date=record['processing_date'],
            reversal_reference=record['reversal_reference'],
            currency=record['currency']
        )
