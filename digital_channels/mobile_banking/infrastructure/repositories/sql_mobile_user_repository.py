"""
SQLite implementation of the mobile user repository interface.
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import sqlite3

from ...domain.entities.mobile_user import MobileBankingUser, RegisteredDevice, UserCredential
from ...application.interfaces.mobile_user_repository_interface import MobileUserRepositoryInterface


class SQLMobileUserRepository(MobileUserRepositoryInterface):
    """SQLite implementation of the mobile user repository."""
    
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
        CREATE TABLE IF NOT EXISTS mobile_banking_users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            mobile_number TEXT UNIQUE NOT NULL,
            email TEXT,
            full_name TEXT,
            customer_id TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL,
            profile_complete INTEGER NOT NULL,
            registration_date TEXT NOT NULL,
            last_login_date TEXT,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_at TEXT,
            credentials TEXT NOT NULL,
            preferences TEXT,
            biometric_enabled INTEGER DEFAULT 0
        )
        ''')
        
        # Create devices table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mobile_banking_devices (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            device_name TEXT,
            device_model TEXT,
            os_version TEXT,
            app_version TEXT,
            registration_date TEXT NOT NULL,
            last_used_date TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES mobile_banking_users (id),
            UNIQUE (user_id, device_id)
        )
        ''')
        
        self._connection.commit()
    
    def get_by_id(self, user_id: UUID) -> Optional[MobileBankingUser]:
        """
        Get a user by their ID.
        
        Args:
            user_id: The ID of the user to get
            
        Returns:
            MobileBankingUser if found, None otherwise
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM mobile_banking_users WHERE id = ?",
            (str(user_id),)
        )
        user_data = cursor.fetchone()
        
        if user_data is None:
            return None
        
        return self._user_from_row(user_data)
    
    def get_by_username(self, username: str) -> Optional[MobileBankingUser]:
        """
        Get a user by their username.
        
        Args:
            username: The username of the user to get
            
        Returns:
            MobileBankingUser if found, None otherwise
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM mobile_banking_users WHERE username = ?",
            (username,)
        )
        user_data = cursor.fetchone()
        
        if user_data is None:
            return None
        
        return self._user_from_row(user_data)
    
    def get_by_mobile_number(self, mobile_number: str) -> Optional[MobileBankingUser]:
        """
        Get a user by their registered mobile number.
        
        Args:
            mobile_number: The mobile number of the user to get
            
        Returns:
            MobileBankingUser if found, None otherwise
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM mobile_banking_users WHERE mobile_number = ?",
            (mobile_number,)
        )
        user_data = cursor.fetchone()
        
        if user_data is None:
            return None
        
        return self._user_from_row(user_data)
    
    def get_by_customer_id(self, customer_id: str) -> Optional[MobileBankingUser]:
        """
        Get a user by their customer ID.
        
        Args:
            customer_id: The customer ID of the user to get
            
        Returns:
            MobileBankingUser if found, None otherwise
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM mobile_banking_users WHERE customer_id = ?",
            (customer_id,)
        )
        user_data = cursor.fetchone()
        
        if user_data is None:
            return None
        
        return self._user_from_row(user_data)
    
    def save(self, user: MobileBankingUser) -> MobileBankingUser:
        """
        Save a user to the repository.
        
        Args:
            user: The user to save
            
        Returns:
            The saved user with any updates (e.g., ID assignment)
        """
        # Assign an ID if the user doesn't have one
        if user.id is None:
            user.id = uuid4()
        
        cursor = self._connection.cursor()
        
        # Convert credentials to JSON
        credentials_json = json.dumps({
            "password_hash": user.credentials.password_hash,
            "salt": user.credentials.salt,
            "hash_algorithm": user.credentials.hash_algorithm,
            "last_changed": user.credentials.last_changed.isoformat() 
                if user.credentials.last_changed else None
        })
        
        # Convert preferences to JSON if present
        preferences_json = json.dumps(user.preferences) if user.preferences else None
        
        # Insert the user
        cursor.execute('''
        INSERT INTO mobile_banking_users 
        (id, username, mobile_number, email, full_name, customer_id, status, 
         profile_complete, registration_date, last_login_date, failed_login_attempts,
         locked_at, credentials, preferences, biometric_enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(user.id),
            user.username,
            user.mobile_number,
            user.email,
            user.full_name,
            user.customer_id,
            user.status,
            1 if user.profile_complete else 0,
            user.registration_date.isoformat() if user.registration_date else None,
            user.last_login_date.isoformat() if user.last_login_date else None,
            user.failed_login_attempts,
            user.locked_at.isoformat() if user.locked_at else None,
            credentials_json,
            preferences_json,
            1 if user.biometric_enabled else 0
        ))
        
        # Insert devices
        for device in user.registered_devices:
            device_id = uuid4() if device.id is None else device.id
            cursor.execute('''
            INSERT INTO mobile_banking_devices
            (id, user_id, device_id, device_name, device_model, os_version, app_version,
             registration_date, last_used_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(device_id),
                str(user.id),
                device.device_id,
                device.device_name,
                device.device_model,
                device.os_version,
                device.app_version,
                device.registration_date.isoformat() if device.registration_date else None,
                device.last_used_date.isoformat() if device.last_used_date else None,
                1 if device.is_active else 0
            ))
            
            # Update the device ID
            device.id = device_id
        
        self._connection.commit()
        return user
    
    def update(self, user: MobileBankingUser) -> MobileBankingUser:
        """
        Update an existing user.
        
        Args:
            user: The user to update
            
        Returns:
            The updated user
        """
        cursor = self._connection.cursor()
        
        # Convert credentials to JSON
        credentials_json = json.dumps({
            "password_hash": user.credentials.password_hash,
            "salt": user.credentials.salt,
            "hash_algorithm": user.credentials.hash_algorithm,
            "last_changed": user.credentials.last_changed.isoformat() 
                if user.credentials.last_changed else None
        })
        
        # Convert preferences to JSON if present
        preferences_json = json.dumps(user.preferences) if user.preferences else None
        
        # Update the user
        cursor.execute('''
        UPDATE mobile_banking_users SET
            username = ?,
            mobile_number = ?,
            email = ?,
            full_name = ?,
            customer_id = ?,
            status = ?,
            profile_complete = ?,
            registration_date = ?,
            last_login_date = ?,
            failed_login_attempts = ?,
            locked_at = ?,
            credentials = ?,
            preferences = ?,
            biometric_enabled = ?
        WHERE id = ?
        ''', (
            user.username,
            user.mobile_number,
            user.email,
            user.full_name,
            user.customer_id,
            user.status,
            1 if user.profile_complete else 0,
            user.registration_date.isoformat() if user.registration_date else None,
            user.last_login_date.isoformat() if user.last_login_date else None,
            user.failed_login_attempts,
            user.locked_at.isoformat() if user.locked_at else None,
            credentials_json,
            preferences_json,
            1 if user.biometric_enabled else 0,
            str(user.id)
        ))
        
        # Delete existing devices
        cursor.execute(
            "DELETE FROM mobile_banking_devices WHERE user_id = ?",
            (str(user.id),)
        )
        
        # Insert updated devices
        for device in user.registered_devices:
            device_id = uuid4() if device.id is None else device.id
            cursor.execute('''
            INSERT INTO mobile_banking_devices
            (id, user_id, device_id, device_name, device_model, os_version, app_version,
             registration_date, last_used_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(device_id),
                str(user.id),
                device.device_id,
                device.device_name,
                device.device_model,
                device.os_version,
                device.app_version,
                device.registration_date.isoformat() if device.registration_date else None,
                device.last_used_date.isoformat() if device.last_used_date else None,
                1 if device.is_active else 0
            ))
            
            # Update the device ID
            device.id = device_id
        
        self._connection.commit()
        return user
    
    def delete(self, user_id: UUID) -> bool:
        """
        Delete a user by their ID.
        
        Args:
            user_id: The ID of the user to delete
            
        Returns:
            True if user was deleted, False otherwise
        """
        cursor = self._connection.cursor()
        
        # Delete devices first
        cursor.execute(
            "DELETE FROM mobile_banking_devices WHERE user_id = ?",
            (str(user_id),)
        )
        
        # Delete user
        cursor.execute(
            "DELETE FROM mobile_banking_users WHERE id = ?",
            (str(user_id),)
        )
        
        self._connection.commit()
        return cursor.rowcount > 0
    
    def list_all(self) -> List[MobileBankingUser]:
        """
        Get all users.
        
        Returns:
            A list of all users
        """
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM mobile_banking_users")
        user_rows = cursor.fetchall()
        
        return [self._user_from_row(row) for row in user_rows]
    
    def _user_from_row(self, row: tuple) -> MobileBankingUser:
        """
        Create a MobileBankingUser from a database row.
        
        Args:
            row: Database row
            
        Returns:
            MobileBankingUser object
        """
        # Extract columns based on order
        (id_str, username, mobile_number, email, full_name, customer_id, status, 
         profile_complete, registration_date_str, last_login_date_str, failed_login_attempts,
         locked_at_str, credentials_json, preferences_json, biometric_enabled) = row
        
        # Parse dates
        registration_date = datetime.fromisoformat(registration_date_str) if registration_date_str else None
        last_login_date = datetime.fromisoformat(last_login_date_str) if last_login_date_str else None
        locked_at = datetime.fromisoformat(locked_at_str) if locked_at_str else None
        
        # Parse credentials
        credentials_dict = json.loads(credentials_json)
        credentials = UserCredential(
            password_hash=credentials_dict["password_hash"],
            salt=credentials_dict["salt"],
            hash_algorithm=credentials_dict["hash_algorithm"],
            last_changed=datetime.fromisoformat(credentials_dict["last_changed"]) 
                if credentials_dict["last_changed"] else None
        )
        
        # Parse preferences
        preferences = json.loads(preferences_json) if preferences_json else None
        
        # Get devices for this user
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM mobile_banking_devices WHERE user_id = ?",
            (id_str,)
        )
        device_rows = cursor.fetchall()
        
        devices = []
        for device_row in device_rows:
            (device_id_str, user_id_str, device_identifier, device_name, device_model, 
             os_version, app_version, registration_date_str, last_used_date_str, is_active) = device_row
            
            device = RegisteredDevice(
                id=UUID(device_id_str),
                device_id=device_identifier,
                device_name=device_name,
                device_model=device_model,
                os_version=os_version,
                app_version=app_version,
                registration_date=datetime.fromisoformat(registration_date_str) 
                    if registration_date_str else None,
                last_used_date=datetime.fromisoformat(last_used_date_str) 
                    if last_used_date_str else None,
                is_active=bool(is_active)
            )
            devices.append(device)
        
        # Create and return user
        return MobileBankingUser(
            id=UUID(id_str),
            username=username,
            mobile_number=mobile_number,
            email=email,
            full_name=full_name,
            customer_id=customer_id,
            status=status,
            profile_complete=bool(profile_complete),
            registration_date=registration_date,
            last_login_date=last_login_date,
            failed_login_attempts=failed_login_attempts,
            locked_at=locked_at,
            credentials=credentials,
            preferences=preferences,
            biometric_enabled=bool(biometric_enabled),
            registered_devices=devices
        )
