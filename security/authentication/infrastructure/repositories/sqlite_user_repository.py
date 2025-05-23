"""
SQLite implementation of the UserRepository interface.
This class provides concrete implementation for user storage and retrieval
using SQLite database.
"""

import sqlite3
from typing import List, Optional
from dataclasses import asdict

from security.authentication.domain.entities.user import User
from security.authentication.domain.value_objects.user_id import UserId
from security.authentication.domain.value_objects.credential import Credential
from security.authentication.domain.value_objects.user_status import UserStatus
from security.authentication.domain.repositories.user_repository import UserRepository
from security.common.security_utils import SecurityException

# Custom exception for database errors
class DatabaseException(SecurityException):
    """Exception raised for database errors"""
    pass


class SQLiteUserRepository(UserRepository):
    """SQLite implementation of the UserRepository interface."""
    
    def __init__(self, db_path: str):
        """Initialize the repository with database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """Create the users table if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    email TEXT UNIQUE,
                    full_name TEXT,
                    status TEXT NOT NULL,
                    failed_login_attempts INTEGER DEFAULT 0,
                    last_login_date TEXT,
                    creation_date TEXT NOT NULL,
                    last_modified_date TEXT NOT NULL,
                    requires_password_change BOOLEAN DEFAULT FALSE
                )
            ''')
            conn.commit()
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to create users table: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def save(self, user: User) -> None:
        """Save a user to the database.
        
        Args:
            user: User entity to save
            
        Raises:
            DatabaseException: If there's an error saving the user
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user.id.value,))
            existing_user = cursor.fetchone()
            
            user_dict = {
                "id": user.id.value,
                "username": user.username,
                "password_hash": user.credential.password_hash,
                "salt": user.credential.salt,
                "email": user.email,
                "full_name": user.full_name,
                "status": user.status.value,
                "failed_login_attempts": user.failed_login_attempts,
                "last_login_date": user.last_login_date,
                "creation_date": user.creation_date,
                "last_modified_date": user.last_modified_date,
                "requires_password_change": user.requires_password_change
            }
            
            if existing_user:
                # Update existing user
                placeholders = ", ".join([f"{field} = ?" for field in user_dict.keys() if field != "id"])
                values = [value for field, value in user_dict.items() if field != "id"]
                values.append(user.id.value)  # For the WHERE clause
                
                cursor.execute(
                    f"UPDATE users SET {placeholders} WHERE id = ?",
                    values
                )
            else:
                # Insert new user
                placeholders = ", ".join(["?"] * len(user_dict))
                fields = ", ".join(user_dict.keys())
                
                cursor.execute(
                    f"INSERT INTO users ({fields}) VALUES ({placeholders})",
                    list(user_dict.values())
                )
                
            conn.commit()
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to save user: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Find a user by ID.
        
        Args:
            user_id: The ID of the user to find
            
        Returns:
            User entity or None if not found
            
        Raises:
            DatabaseException: If there's an error retrieving the user
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id.value,)
            )
            user_data = cursor.fetchone()
            
            if not user_data:
                return None
                
            column_names = [description[0] for description in cursor.description]
            user_dict = dict(zip(column_names, user_data))
            
            return self._map_to_user(user_dict)
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to find user by ID: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by username.
        
        Args:
            username: The username to search for
            
        Returns:
            User entity or None if not found
            
        Raises:
            DatabaseException: If there's an error retrieving the user
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            user_data = cursor.fetchone()
            
            if not user_data:
                return None
                
            column_names = [description[0] for description in cursor.description]
            user_dict = dict(zip(column_names, user_data))
            
            return self._map_to_user(user_dict)
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to find user by username: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address.
        
        Args:
            email: The email address to search for
            
        Returns:
            User entity or None if not found
            
        Raises:
            DatabaseException: If there's an error retrieving the user
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            )
            user_data = cursor.fetchone()
            
            if not user_data:
                return None
                
            column_names = [description[0] for description in cursor.description]
            user_dict = dict(zip(column_names, user_data))
            
            return self._map_to_user(user_dict)
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to find user by email: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def find_all(self) -> List[User]:
        """Find all users in the database.
        
        Returns:
            List of User entities
            
        Raises:
            DatabaseException: If there's an error retrieving users
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users")
            users_data = cursor.fetchall()
            
            column_names = [description[0] for description in cursor.description]
            users = []
            
            for user_data in users_data:
                user_dict = dict(zip(column_names, user_data))
                users.append(self._map_to_user(user_dict))
                
            return users
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to find all users: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def delete(self, user_id: UserId) -> None:
        """Delete a user from the database.
        
        Args:
            user_id: The ID of the user to delete
            
        Raises:
            DatabaseException: If there's an error deleting the user
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM users WHERE id = ?",
                (user_id.value,)
            )
            conn.commit()
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to delete user: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def _map_to_user(self, user_dict: dict) -> User:
        """Map database record to User entity.
        
        Args:
            user_dict: Dictionary containing user data from database
            
        Returns:
            User entity
        """
        return User(
            user_id=UserId(user_dict["id"]),
            username=user_dict["username"],
            credential=Credential(
                password_hash=user_dict["password_hash"],
                salt=user_dict["salt"]
            ),
            email=user_dict["email"],
            full_name=user_dict["full_name"],
            status=UserStatus(user_dict["status"]),
            failed_login_attempts=user_dict["failed_login_attempts"],
            last_login_date=user_dict["last_login_date"],
            creation_date=user_dict["creation_date"],
            last_modified_date=user_dict["last_modified_date"],
            requires_password_change=bool(user_dict["requires_password_change"])
        )
