"""
Account Services Module

This module provides core functionality for different account types.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from enum import Enum, auto

# Use centralized import system
from utils.lib.packages import fix_path, import_module, get_database_connection
fix_path()  # Ensures the project root is in sys.path


try:
    from core_banking.database.db_helper import execute_query, execute_transaction
except ImportError:
    # Try to import from database module directly
    try:
        from core_banking.database.connection import DatabaseConnection
        
        def execute_query(query, params=None, fetch_all=True):
            conn = DatabaseConnection().get_connection()
            if not conn:
                return None
                
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params or ())
                
                if fetch_all:
                    return cursor.fetchall()
                else:
                    return cursor.fetchone()
            finally:
                if 'cursor' in locals():
                    cursor.close()
                    
        def execute_transaction(queries):
            conn = DatabaseConnection().get_connection()
            if not conn:
                return False
                
            try:
                cursor = conn.cursor()
                conn.autocommit = False
                
                for query, params in queries:
                    cursor.execute(query, params or ())
                    
                conn.commit()
                return True
            except Exception as e:
                if conn:
                    conn.rollback()
                return False
            finally:
                if 'cursor' in locals():
                    cursor.close()
                if conn:
                    conn.autocommit = True
    except ImportError:
        # Provide mock functions if all imports fail
        def execute_query(query, params=None, fetch_all=True):
            print(f"MOCK: Would execute query: {query}")
            return []
            
        def execute_transaction(queries):
            print(f"MOCK: Would execute transaction with {len(queries)} queries")
            return True


class AccountType(Enum):
    """Enumeration of supported account types"""
    SAVINGS = auto()
    CURRENT = auto()
    FIXED_DEPOSIT = auto()
    RECURRING_DEPOSIT = auto()
    LOAN = auto()


class AccountStatus(Enum):
    """Enumeration of possible account statuses"""
    ACTIVE = auto()
    INACTIVE = auto()
    DORMANT = auto()
    CLOSED = auto()
    FROZEN = auto()


class AccountService:
    """Base class for account-related services"""
    
    def __init__(self, account_id=None):
        self.account_id = account_id
        self.account_data = None
        
        if account_id:
            self.load_account()
    
    def load_account(self):
        """Load account data from database"""
        if not self.account_id:
            return False
            
        query = """
            SELECT * FROM accounts 
            WHERE account_id = %s OR account_number = %s
        """
        
        self.account_data = execute_query(
            query, 
            (self.account_id, self.account_id), 
            fetch_all=False
        )
        
        return bool(self.account_data)
    
    def get_balance(self):
        """Get current account balance"""
        if not self.account_data:
            return 0.0
            
        return float(self.account_data.get('balance', 0.0))
    
    def get_transactions(self, limit=50):
        """Get recent transactions for this account"""
        if not self.account_id:
            return []
            
        query = """
            SELECT * FROM transactions
            WHERE account_id = %s
            ORDER BY transaction_date DESC
            LIMIT %s
        """
        
        return execute_query(query, (self.account_id, limit))
    
    def update_balance(self, new_balance):
        """Update account balance"""
        if not self.account_id:
            return False
            
        query = """
            UPDATE accounts
            SET balance = %s,
                updated_at = %s
            WHERE account_id = %s
        """
        
        result = execute_transaction([
            (query, (new_balance, datetime.now(), self.account_id))
        ])
        
        if result:
            # Update local cache
            if self.account_data:
                self.account_data['balance'] = new_balance
                
        return result