"""
SQL Account Repository

This module implements the account repository using SQL database.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from ....domain.entities.account import Account, AccountType, AccountStatus
from ...interfaces.account_repository import AccountRepositoryInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class SqlAccountRepository(AccountRepositoryInterface):
    """SQL implementation of account repository"""
    
    def __init__(self, db_connection):
        """
        Initialize repository with database connection
        
        Args:
            db_connection: Database connection object
        """
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
    
    def create(self, account: Account) -> Account:
        """
        Create a new account
        
        Args:
            account: The account to create
            
        Returns:
            The created account
        """
        try:
            query = """
                INSERT INTO accounts (
                    id, account_number, customer_id, account_type, 
                    balance, status, currency, created_at, updated_at,
                    interest_rate, overdraft_limit
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            params = (
                str(account.id),
                account.account_number,
                str(account.customer_id),
                account.account_type.value,
                float(account.balance),
                account.status.value,
                account.currency,
                account.created_at,
                account.updated_at,
                float(account.interest_rate) if account.interest_rate else None,
                float(account.overdraft_limit) if account.overdraft_limit else None
            )
            
            with self.db.cursor() as cursor:
                cursor.execute(query, params)
                self.db.commit()
                
            return account
        except Exception as e:
            self.logger.error(f"Error creating account: {e}")
            self.db.rollback()
            raise
    
    def get_by_id(self, account_id: UUID) -> Optional[Account]:
        """
        Get an account by ID
        
        Args:
            account_id: The account ID
            
        Returns:
            The account if found, None otherwise
        """
        try:
            query = """
                SELECT 
                    id, account_number, customer_id, account_type, 
                    balance, status, currency, created_at, updated_at,
                    interest_rate, overdraft_limit
                FROM accounts
                WHERE id = %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (str(account_id),))
                result = cursor.fetchone()
                
                if not result:
                    return None
                    
                return self._map_row_to_entity(result)
        except Exception as e:
            self.logger.error(f"Error getting account by ID: {e}")
            raise
    
    def get_by_account_number(self, account_number: str) -> Optional[Account]:
        """
        Get an account by account number
        
        Args:
            account_number: The account number
            
        Returns:
            The account if found, None otherwise
        """
        try:
            query = """
                SELECT 
                    id, account_number, customer_id, account_type, 
                    balance, status, currency, created_at, updated_at,
                    interest_rate, overdraft_limit
                FROM accounts
                WHERE account_number = %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (account_number,))
                result = cursor.fetchone()
                
                if not result:
                    return None
                    
                return self._map_row_to_entity(result)
        except Exception as e:
            self.logger.error(f"Error getting account by number: {e}")
            raise
    
    def get_by_customer_id(self, customer_id: UUID) -> List[Account]:
        """
        Get accounts by customer ID
        
        Args:
            customer_id: The customer ID
            
        Returns:
            List of accounts
        """
        try:
            query = """
                SELECT 
                    id, account_number, customer_id, account_type, 
                    balance, status, currency, created_at, updated_at,
                    interest_rate, overdraft_limit
                FROM accounts
                WHERE customer_id = %s
                ORDER BY created_at DESC
            """
            
            accounts = []
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (str(customer_id),))
                results = cursor.fetchall()
                
                for row in results:
                    accounts.append(self._map_row_to_entity(row))
                    
                return accounts
        except Exception as e:
            self.logger.error(f"Error getting accounts by customer ID: {e}")
            raise
    
    def update(self, account: Account) -> Account:
        """
        Update an account
        
        Args:
            account: The account to update
            
        Returns:
            The updated account
        """
        try:
            query = """
                UPDATE accounts
                SET 
                    balance = %s,
                    status = %s,
                    updated_at = %s,
                    interest_rate = %s,
                    overdraft_limit = %s
                WHERE id = %s
            """
            
            account.updated_at = datetime.now()
            
            params = (
                float(account.balance),
                account.status.value,
                account.updated_at,
                float(account.interest_rate) if account.interest_rate else None,
                float(account.overdraft_limit) if account.overdraft_limit else None,
                str(account.id)
            )
            
            with self.db.cursor() as cursor:
                cursor.execute(query, params)
                self.db.commit()
                
            return account
        except Exception as e:
            self.logger.error(f"Error updating account: {e}")
            self.db.rollback()
            raise
    
    def update_balance(self, account_id: UUID, balance: Decimal) -> bool:
        """
        Update account balance
        
        Args:
            account_id: The account ID
            balance: The new balance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE accounts
                SET 
                    balance = %s,
                    updated_at = %s
                WHERE id = %s
            """
            
            params = (
                float(balance),
                datetime.now(),
                str(account_id)
            )
            
            with self.db.cursor() as cursor:
                cursor.execute(query, params)
                self.db.commit()
                
            return True
        except Exception as e:
            self.logger.error(f"Error updating account balance: {e}")
            self.db.rollback()
            return False
    
    def update_status(self, account_id: UUID, status: AccountStatus) -> bool:
        """
        Update account status
        
        Args:
            account_id: The account ID
            status: The new status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE accounts
                SET 
                    status = %s,
                    updated_at = %s
                WHERE id = %s
            """
            
            params = (
                status.value,
                datetime.now(),
                str(account_id)
            )
            
            with self.db.cursor() as cursor:
                cursor.execute(query, params)
                self.db.commit()
                
            return True
        except Exception as e:
            self.logger.error(f"Error updating account status: {e}")
            self.db.rollback()
            return False
    
    def delete(self, account_id: UUID) -> bool:
        """
        Delete an account (logical delete by setting status to CLOSED)
        
        Args:
            account_id: The account ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # We implement a logical delete by setting status to CLOSED
            return self.update_status(account_id, AccountStatus.CLOSED)
        except Exception as e:
            self.logger.error(f"Error deleting account: {e}")
            return False
    
    def search(self, 
              account_type: Optional[AccountType] = None,
              status: Optional[AccountStatus] = None,
              min_balance: Optional[Decimal] = None,
              max_balance: Optional[Decimal] = None,
              created_after: Optional[datetime] = None,
              created_before: Optional[datetime] = None) -> List[Account]:
        """
        Search accounts by criteria
        
        Args:
            account_type: Filter by account type
            status: Filter by account status
            min_balance: Minimum balance
            max_balance: Maximum balance
            created_after: Created after date
            created_before: Created before date
            
        Returns:
            List of matching accounts
        """
        try:
            query = """
                SELECT 
                    id, account_number, customer_id, account_type, 
                    balance, status, currency, created_at, updated_at,
                    interest_rate, overdraft_limit
                FROM accounts
                WHERE 1=1
            """
            
            params = []
            
            if account_type:
                query += " AND account_type = %s"
                params.append(account_type.value)
                
            if status:
                query += " AND status = %s"
                params.append(status.value)
                
            if min_balance is not None:
                query += " AND balance >= %s"
                params.append(float(min_balance))
                
            if max_balance is not None:
                query += " AND balance <= %s"
                params.append(float(max_balance))
                
            if created_after:
                query += " AND created_at >= %s"
                params.append(created_after)
                
            if created_before:
                query += " AND created_at <= %s"
                params.append(created_before)
                
            query += " ORDER BY created_at DESC"
            
            accounts = []
            
            with self.db.cursor() as cursor:
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()
                
                for row in results:
                    accounts.append(self._map_row_to_entity(row))
                    
                return accounts
        except Exception as e:
            self.logger.error(f"Error searching accounts: {e}")
            raise
    
    def _map_row_to_entity(self, row) -> Account:
        """
        Map a database row to an Account entity
        
        Args:
            row: The database row
            
        Returns:
            An Account entity
        """
        id_val, account_number, customer_id, account_type, balance, status, currency, \
        created_at, updated_at, interest_rate, overdraft_limit = row
        
        return Account(
            id=UUID(id_val),
            account_number=account_number,
            customer_id=UUID(customer_id),
            account_type=AccountType(account_type),
            balance=Decimal(str(balance)),
            status=AccountStatus(status),
            currency=currency,
            created_at=created_at,
            updated_at=updated_at,
            interest_rate=Decimal(str(interest_rate)) if interest_rate is not None else None,
            overdraft_limit=Decimal(str(overdraft_limit)) if overdraft_limit is not None else None
        )
