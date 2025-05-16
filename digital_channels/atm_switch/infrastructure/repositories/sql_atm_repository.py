"""
SQL ATM Repository

This module implements the ATM repository interface using SQL database.
"""

import logging
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from datetime import datetime, date, timedelta

from ....domain.entities.atm_card import AtmCard
from ....domain.entities.atm_session import AtmSession
from ....domain.entities.transaction import Transaction
from ....domain.entities.account import Account
from ...application.interfaces.atm_repository import AtmRepository


class SqlAtmRepository(AtmRepository):
    """SQL implementation of ATM repository"""
    
    def __init__(self, db_connection):
        """
        Initialize repository with database connection
        
        Args:
            db_connection: Database connection object
        """
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
    
    def get_card_by_number(self, card_number: str) -> Optional[AtmCard]:
        """
        Get card by card number
        
        Args:
            card_number: Card number
            
        Returns:
            Card if found, None otherwise
        """
        try:
            query = """
                SELECT 
                    card_number, account_id, expiry_date, is_active, 
                    failed_pin_attempts, status, last_used_at
                FROM atm_cards
                WHERE card_number = %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (card_number,))
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                return AtmCard(
                    card_number=result[0],
                    account_id=result[1],
                    expiry_date=result[2],
                    is_active=result[3],
                    failed_pin_attempts=result[4],
                    status=result[5],
                    last_used_at=result[6]
                )
                
        except Exception as e:
            self.logger.error(f"Error fetching card: {e}")
            return None
    
    def get_session_by_token(self, session_token: str) -> Optional[AtmSession]:
        """
        Get session by token
        
        Args:
            session_token: Session token
            
        Returns:
            Session if found, None otherwise
        """
        try:
            query = """
                SELECT 
                    session_token, card_number, account_id, 
                    expiry_time, created_at
                FROM atm_sessions
                WHERE session_token = %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (session_token,))
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                return AtmSession(
                    session_token=result[0],
                    card_number=result[1],
                    account_id=result[2],
                    expiry_time=result[3],
                    created_at=result[4]
                )
                
        except Exception as e:
            self.logger.error(f"Error fetching session: {e}")
            return None
    
    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """
        Get account by ID
        
        Args:
            account_id: Account ID
            
        Returns:
            Account if found, None otherwise
        """
        try:
            query = """
                SELECT 
                    account_id, account_number, customer_id,
                    balance, account_type, status, 
                    created_at, updated_at
                FROM accounts
                WHERE account_id = %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (account_id,))
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                return Account(
                    account_id=result[0],
                    account_number=result[1],
                    customer_id=result[2],
                    balance=result[3],
                    account_type=result[4],
                    status=result[5],
                    created_at=result[6],
                    updated_at=result[7]
                )
                
        except Exception as e:
            self.logger.error(f"Error fetching account: {e}")
            return None
    
    def save_transaction(self, transaction: Transaction) -> bool:
        """
        Save transaction to the repository
        
        Args:
            transaction: Transaction to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                INSERT INTO transactions (
                    transaction_id, account_id, amount, 
                    transaction_type, description, fee,
                    balance_before, balance_after, status,
                    created_at, completed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                transaction.transaction_id,
                transaction.account_id,
                transaction.amount,
                transaction.transaction_type,
                transaction.description,
                transaction.fee,
                transaction.balance_before,
                transaction.balance_after,
                transaction.status,
                transaction.created_at,
                transaction.completed_at
            )
            
            with self.db.cursor() as cursor:
                cursor.execute(query, values)
                self.db.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving transaction: {e}")
            self.db.rollback()
            return False
    
    def update_account_balance(self, account_id: int, new_balance: Decimal) -> bool:
        """
        Update account balance
        
        Args:
            account_id: Account ID
            new_balance: New account balance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE accounts
                SET balance = %s, updated_at = %s
                WHERE account_id = %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (new_balance, datetime.now(), account_id))
                self.db.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating account balance: {e}")
            self.db.rollback()
            return False
    
    def update_card_status(self, card_number: str, status: str) -> bool:
        """
        Update card status
        
        Args:
            card_number: Card number
            status: New card status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE atm_cards
                SET status = %s
                WHERE card_number = %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (status, card_number))
                self.db.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating card status: {e}")
            self.db.rollback()
            return False
    
    def update_card(self, card: AtmCard) -> bool:
        """
        Update card in repository
        
        Args:
            card: Card to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE atm_cards
                SET
                    is_active = %s,
                    failed_pin_attempts = %s,
                    status = %s,
                    last_used_at = %s
                WHERE card_number = %s
            """
            
            values = (
                card.is_active,
                card.failed_pin_attempts,
                card.status,
                card.last_used_at,
                card.card_number
            )
            
            with self.db.cursor() as cursor:
                cursor.execute(query, values)
                self.db.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating card: {e}")
            self.db.rollback()
            return False
    
    def get_transactions_by_account(
        self, account_id: int, start_date: Optional[date] = None, 
        end_date: Optional[date] = None, limit: int = 10
    ) -> List[Transaction]:
        """
        Get transactions by account
        
        Args:
            account_id: Account ID
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of transactions to return
            
        Returns:
            List of transactions
        """
        try:
            if start_date is None:
                start_date = date.today() - timedelta(days=30)  # Default to last 30 days
                
            if end_date is None:
                end_date = date.today() + timedelta(days=1)  # Include today
            
            query = """
                SELECT 
                    transaction_id, account_id, amount, 
                    transaction_type, description, fee,
                    balance_before, balance_after, status,
                    created_at, completed_at
                FROM transactions
                WHERE account_id = %s
                AND created_at >= %s
                AND created_at <= %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (account_id, start_date, end_date, limit))
                results = cursor.fetchall()
                
                transactions = []
                for row in results:
                    transaction = Transaction(
                        transaction_id=row[0],
                        account_id=row[1],
                        amount=row[2],
                        transaction_type=row[3],
                        description=row[4],
                        fee=row[5]
                    )
                    
                    # Set other attributes
                    transaction.balance_before = row[6]
                    transaction.balance_after = row[7]
                    transaction.status = row[8]
                    transaction.created_at = row[9]
                    transaction.completed_at = row[10]
                    
                    transactions.append(transaction)
                
                return transactions
                
        except Exception as e:
            self.logger.error(f"Error getting transactions: {e}")
            return []
    
    def get_today_withdrawals(self, account_id: int) -> Decimal:
        """
        Get total withdrawals for today
        
        Args:
            account_id: Account ID
            
        Returns:
            Total withdrawal amount for today
        """
        try:
            today = date.today()
            tomorrow = today + timedelta(days=1)
            
            query = """
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE account_id = %s
                AND transaction_type = 'ATM_WITHDRAWAL'
                AND created_at >= %s
                AND created_at < %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (account_id, today, tomorrow))
                result = cursor.fetchone()
                
                return Decimal(result[0]) if result and result[0] else Decimal('0')
                
        except Exception as e:
            self.logger.error(f"Error getting today's withdrawals: {e}")
            return Decimal('0')
    
    def get_monthly_withdrawals_count(self, account_id: int) -> int:
        """
        Get count of withdrawals for the current month
        
        Args:
            account_id: Account ID
            
        Returns:
            Number of withdrawals in current month
        """
        try:
            today = date.today()
            first_day = date(today.year, today.month, 1)
            
            if today.month == 12:
                next_month = date(today.year + 1, 1, 1)
            else:
                next_month = date(today.year, today.month + 1, 1)
            
            query = """
                SELECT COUNT(*) as count
                FROM transactions
                WHERE account_id = %s
                AND transaction_type = 'ATM_WITHDRAWAL'
                AND created_at >= %s
                AND created_at < %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (account_id, first_day, next_month))
                result = cursor.fetchone()
                
                return int(result[0]) if result and result[0] else 0
                
        except Exception as e:
            self.logger.error(f"Error getting monthly withdrawals count: {e}")
            return 0
    
    def update_pin(self, card_number: str, pin_hash: str, salt: str) -> bool:
        """
        Update card PIN hash
        
        Args:
            card_number: Card number
            pin_hash: New PIN hash
            salt: Salt used for hashing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE card_security
                SET pin_hash = %s, salt = %s, updated_at = %s
                WHERE card_number = %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (pin_hash, salt, datetime.now(), card_number))
                self.db.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating PIN: {e}")
            self.db.rollback()
            return False
