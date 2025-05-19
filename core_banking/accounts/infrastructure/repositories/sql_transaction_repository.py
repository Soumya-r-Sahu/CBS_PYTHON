"""
SQL Transaction Repository

This module implements the transaction repository using SQL database.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from ....domain.entities.transaction import Transaction, TransactionType, TransactionStatus
from ...interfaces.transaction_repository import TransactionRepositoryInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



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
            transaction: The transaction to create
            
        Returns:
            The created transaction
        """
        try:
            query = """
                INSERT INTO transactions (
                    id, account_id, transaction_type, amount, status,
                    reference_id, description, timestamp, balance_after,
                    fee, source_account, destination_account
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            params = (
                str(transaction.id),
                transaction.account_id,
                transaction.transaction_type.value,
                float(transaction.amount),
                transaction.status.value,
                transaction.reference_id,
                transaction.description,
                transaction.timestamp,
                float(transaction.balance_after) if transaction.balance_after is not None else None,
                float(transaction.fee),
                transaction.source_account,
                transaction.destination_account
            )
            
            with self.db.cursor() as cursor:
                cursor.execute(query, params)
                self.db.commit()
                
            return transaction
        except Exception as e:
            self.logger.error(f"Error creating transaction: {e}")
            self.db.rollback()
            raise
    
    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """
        Get a transaction by ID
        
        Args:
            transaction_id: The transaction ID
            
        Returns:
            The transaction if found, None otherwise
        """
        try:
            query = """
                SELECT 
                    id, account_id, transaction_type, amount, status,
                    reference_id, description, timestamp, balance_after,
                    fee, source_account, destination_account
                FROM transactions
                WHERE id = %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (str(transaction_id),))
                result = cursor.fetchone()
                
                if not result:
                    return None
                    
                return self._map_row_to_entity(result)
        except Exception as e:
            self.logger.error(f"Error getting transaction by ID: {e}")
            raise
    
    def get_by_account_id(self, 
                         account_id: str, 
                         limit: int = 10, 
                         offset: int = 0) -> List[Transaction]:
        """
        Get transactions by account ID
        
        Args:
            account_id: The account ID
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of transactions
        """
        try:
            query = """
                SELECT 
                    id, account_id, transaction_type, amount, status,
                    reference_id, description, timestamp, balance_after,
                    fee, source_account, destination_account
                FROM transactions
                WHERE account_id = %s
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """
            
            transactions = []
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (account_id, limit, offset))
                results = cursor.fetchall()
                
                for row in results:
                    transactions.append(self._map_row_to_entity(row))
                    
                return transactions
        except Exception as e:
            self.logger.error(f"Error getting transactions by account ID: {e}")
            raise
    
    def get_by_reference_id(self, reference_id: str) -> List[Transaction]:
        """
        Get transactions by reference ID
        
        Args:
            reference_id: The reference ID
            
        Returns:
            List of transactions
        """
        try:
            query = """
                SELECT 
                    id, account_id, transaction_type, amount, status,
                    reference_id, description, timestamp, balance_after,
                    fee, source_account, destination_account
                FROM transactions
                WHERE reference_id = %s
                ORDER BY timestamp DESC
            """
            
            transactions = []
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (reference_id,))
                results = cursor.fetchall()
                
                for row in results:
                    transactions.append(self._map_row_to_entity(row))
                    
                return transactions
        except Exception as e:
            self.logger.error(f"Error getting transactions by reference ID: {e}")
            raise
    
    def update_status(self, transaction_id: UUID, status: TransactionStatus) -> bool:
        """
        Update transaction status
        
        Args:
            transaction_id: The transaction ID
            status: The new status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE transactions
                SET status = %s
                WHERE id = %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (status.value, str(transaction_id)))
                self.db.commit()
                
            return True
        except Exception as e:
            self.logger.error(f"Error updating transaction status: {e}")
            self.db.rollback()
            return False
    
    def search(self,
              account_id: Optional[str] = None,
              transaction_type: Optional[TransactionType] = None,
              status: Optional[TransactionStatus] = None,
              min_amount: Optional[Decimal] = None,
              max_amount: Optional[Decimal] = None,
              start_date: Optional[datetime] = None,
              end_date: Optional[datetime] = None,
              limit: int = 100,
              offset: int = 0) -> List[Transaction]:
        """
        Search transactions by criteria
        
        Args:
            account_id: Filter by account ID
            transaction_type: Filter by transaction type
            status: Filter by transaction status
            min_amount: Minimum amount
            max_amount: Maximum amount
            start_date: Start date
            end_date: End date
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of matching transactions
        """
        try:
            query = """
                SELECT 
                    id, account_id, transaction_type, amount, status,
                    reference_id, description, timestamp, balance_after,
                    fee, source_account, destination_account
                FROM transactions
                WHERE 1=1
            """
            
            params = []
            
            if account_id:
                query += " AND account_id = %s"
                params.append(account_id)
                
            if transaction_type:
                query += " AND transaction_type = %s"
                params.append(transaction_type.value)
                
            if status:
                query += " AND status = %s"
                params.append(status.value)
                
            if min_amount is not None:
                query += " AND amount >= %s"
                params.append(float(min_amount))
                
            if max_amount is not None:
                query += " AND amount <= %s"
                params.append(float(max_amount))
                
            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)
                
            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)
                
            query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
            params.append(limit)
            params.append(offset)
            
            transactions = []
            
            with self.db.cursor() as cursor:
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()
                
                for row in results:
                    transactions.append(self._map_row_to_entity(row))
                    
                return transactions
        except Exception as e:
            self.logger.error(f"Error searching transactions: {e}")
            raise
    
    def _map_row_to_entity(self, row) -> Transaction:
        """
        Map a database row to a Transaction entity
        
        Args:
            row: The database row
            
        Returns:
            A Transaction entity
        """
        id_val, account_id, transaction_type, amount, status, reference_id, \
        description, timestamp, balance_after, fee, source_account, destination_account = row
        
        return Transaction(
            id=UUID(id_val),
            account_id=account_id,
            transaction_type=TransactionType(transaction_type),
            amount=Decimal(str(amount)),
            status=TransactionStatus(status),
            reference_id=reference_id,
            description=description,
            timestamp=timestamp,
            balance_after=Decimal(str(balance_after)) if balance_after is not None else None,
            fee=Decimal(str(fee)) if fee is not None else Decimal('0.00'),
            source_account=source_account,
            destination_account=destination_account
        )
