"""
SQL-based user repository implementation for the Internet Banking domain.
"""
from typing import Optional, List
from uuid import UUID
import sqlite3

from ...domain.entities.user import InternetBankingUser, UserCredential, UserStatus
from ...application.interfaces.user_repository_interface import UserRepositoryInterface


class SQLUserRepository(UserRepositoryInterface):
    """SQL implementation of the user repository."""
    
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
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS internet_banking_users (
            user_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            email TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT,
            last_password_change TEXT NOT NULL,
            failed_login_attempts INTEGER DEFAULT 0
        )
        ''')
        
        # Create devices table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS internet_banking_user_devices (
            user_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            PRIMARY KEY (user_id, device_id),
            FOREIGN KEY (user_id) REFERENCES internet_banking_users(user_id)
        )
        ''')
        
        self._connection.commit()
    
    def get_by_id(self, user_id: UUID) -> Optional[InternetBankingUser]:
        """
        Get a user by their ID.
        
        Args:
            user_id: The ID of the user to get
            
        Returns:
            InternetBankingUser if found, None otherwise
        """
        cursor = self._connection.cursor()
        
        # Get user from database
        cursor.execute(
            "SELECT * FROM internet_banking_users WHERE user_id = ?",
            (str(user_id),)
        )
        
        user_row = cursor.fetchone()
        if user_row is None:
            return None
        
        # Get devices for user
        cursor.execute(
            "SELECT device_id FROM internet_banking_user_devices WHERE user_id = ?",
            (str(user_id),)
        )
        
        devices = [row[0] for row in cursor.fetchall()]
        
        # Convert row to InternetBankingUser object
        return self._row_to_user(user_row, devices)
    
    def get_by_username(self, username: str) -> Optional[InternetBankingUser]:
        """
        Get a user by their username.
        
        Args:
            username: The username to search for
            
        Returns:
            InternetBankingUser if found, None otherwise
        """
        cursor = self._connection.cursor()
        
        # Get user from database
        cursor.execute(
            "SELECT * FROM internet_banking_users WHERE username = ?",
            (username,)
        )
        
        user_row = cursor.fetchone()
        if user_row is None:
            return None
        
        # Get devices for user
        cursor.execute(
            "SELECT device_id FROM internet_banking_user_devices WHERE user_id = ?",
            (user_row[0],)  # user_id is the first column
        )
        
        devices = [row[0] for row in cursor.fetchall()]
        
        # Convert row to InternetBankingUser object
        return self._row_to_user(user_row, devices)
    
    def get_by_customer_id(self, customer_id: UUID) -> Optional[InternetBankingUser]:
        """
        Get a user by their associated customer ID.
        
        Args:
            customer_id: The customer ID to search for
            
        Returns:
            InternetBankingUser if found, None otherwise
        """
        cursor = self._connection.cursor()
        
        # Get user from database
        cursor.execute(
            "SELECT * FROM internet_banking_users WHERE customer_id = ?",
            (str(customer_id),)
        )
        
        user_row = cursor.fetchone()
        if user_row is None:
            return None
        
        # Get devices for user
        cursor.execute(
            "SELECT device_id FROM internet_banking_user_devices WHERE user_id = ?",
            (user_row[0],)  # user_id is the first column
        )
        
        devices = [row[0] for row in cursor.fetchall()]
        
        # Convert row to InternetBankingUser object
        return self._row_to_user(user_row, devices)
    
    def save(self, user: InternetBankingUser) -> InternetBankingUser:
        """
        Save or update a user.
        
        Args:
            user: The user to save
            
        Returns:
            The saved user (with any generated IDs if it's a new user)
        """
        cursor = self._connection.cursor()
        
        # Check if user exists
        cursor.execute(
            "SELECT COUNT(*) FROM internet_banking_users WHERE user_id = ?",
            (str(user.user_id),)
        )
        
        user_exists = cursor.fetchone()[0] > 0
        
        if user_exists:
            # Update existing user
            cursor.execute(
                """
                UPDATE internet_banking_users SET
                email = ?,
                phone_number = ?,
                username = ?,
                password_hash = ?,
                salt = ?,
                status = ?,
                last_login = ?,
                last_password_change = ?,
                failed_login_attempts = ?
                WHERE user_id = ?
                """,
                (
                    user.email,
                    user.phone_number,
                    user.credentials.username,
                    user.credentials.password_hash,
                    user.credentials.salt,
                    user.status.value,
                    user.last_login.isoformat() if user.last_login else None,
                    user.credentials.last_password_change.isoformat(),
                    user.credentials.failed_login_attempts,
                    str(user.user_id)
                )
            )
        else:
            # Insert new user
            cursor.execute(
                """
                INSERT INTO internet_banking_users (
                user_id, customer_id, email, phone_number, username,
                password_hash, salt, status, created_at, last_login,
                last_password_change, failed_login_attempts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(user.user_id),
                    str(user.customer_id),
                    user.email,
                    user.phone_number,
                    user.credentials.username,
                    user.credentials.password_hash,
                    user.credentials.salt,
                    user.status.value,
                    user.created_at.isoformat(),
                    user.last_login.isoformat() if user.last_login else None,
                    user.credentials.last_password_change.isoformat(),
                    user.credentials.failed_login_attempts
                )
            )
        
        # Delete existing devices and insert new ones
        cursor.execute(
            "DELETE FROM internet_banking_user_devices WHERE user_id = ?",
            (str(user.user_id),)
        )
        
        for device_id in user.registered_devices:
            cursor.execute(
                "INSERT INTO internet_banking_user_devices (user_id, device_id) VALUES (?, ?)",
                (str(user.user_id), device_id)
            )
        
        self._connection.commit()
        
        # Return user with same ID
        return user
    
    def delete(self, user_id: UUID) -> bool:
        """
        Delete a user by their ID.
        
        Args:
            user_id: The ID of the user to delete
            
        Returns:
            True if the user was deleted, False otherwise
        """
        cursor = self._connection.cursor()
        
        # Delete devices first (foreign key constraint)
        cursor.execute(
            "DELETE FROM internet_banking_user_devices WHERE user_id = ?",
            (str(user_id),)
        )
        
        # Delete user
        cursor.execute(
            "DELETE FROM internet_banking_users WHERE user_id = ?",
            (str(user_id),)
        )
        
        self._connection.commit()
        
        # Check if any rows were affected
        return cursor.rowcount > 0
    
    def list_active_users(self) -> List[InternetBankingUser]:
        """
        Get a list of all active users.
        
        Returns:
            List of active InternetBankingUser objects
        """
        cursor = self._connection.cursor()
        
        # Get all active users
        cursor.execute(
            "SELECT * FROM internet_banking_users WHERE status = ?",
            (UserStatus.ACTIVE.value,)
        )
        
        user_rows = cursor.fetchall()
        users = []
        
        for user_row in user_rows:
            # Get devices for user
            cursor.execute(
                "SELECT device_id FROM internet_banking_user_devices WHERE user_id = ?",
                (user_row[0],)  # user_id is the first column
            )
            
            devices = [row[0] for row in cursor.fetchall()]
            
            # Convert row to InternetBankingUser object
            users.append(self._row_to_user(user_row, devices))
        
        return users
    
    def _row_to_user(self, row, devices) -> InternetBankingUser:
        """
        Convert a database row to an InternetBankingUser object.
        
        Args:
            row: Database row from the internet_banking_users table
            devices: List of device IDs for the user
            
        Returns:
            InternetBankingUser object
        """
        from datetime import datetime
        
        # Create UserCredential
        credentials = UserCredential(
            username=row[4],  # username
            password_hash=row[5],  # password_hash
            salt=row[6],  # salt
            last_password_change=datetime.fromisoformat(row[10]),  # last_password_change
            failed_login_attempts=row[11]  # failed_login_attempts
        )
        
        # Create InternetBankingUser
        return InternetBankingUser(
            user_id=UUID(row[0]),  # user_id
            customer_id=UUID(row[1]),  # customer_id
            email=row[2],  # email
            phone_number=row[3],  # phone_number
            credentials=credentials,
            status=UserStatus(row[7]),  # status
            created_at=datetime.fromisoformat(row[8]),  # created_at
            last_login=datetime.fromisoformat(row[9]) if row[9] else None,  # last_login
            registered_devices=devices
        )
