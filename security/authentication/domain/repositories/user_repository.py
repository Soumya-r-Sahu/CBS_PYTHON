"""
User Repository Interface

This module defines the repository interface for user data access.
It follows the repository pattern from Domain-Driven Design.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.user import User
from ..value_objects.user_id import UserId


class UserRepository(ABC):
    """
    Interface for user data access operations
    
    This abstract class defines the contract that any user
    repository implementation must follow.
    """
    
    @abstractmethod
    def get_by_id(self, id: UUID) -> Optional[User]:
        """
        Retrieve a user by their UUID
        
        Args:
            id: The UUID of the user
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: UserId) -> Optional[User]:
        """
        Retrieve a user by their business identifier
        
        Args:
            user_id: The business identifier of the user
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user by their username
        
        Args:
            username: The username to look up
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address
        
        Args:
            email: The email address to look up
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[User]:
        """
        Retrieve all users
        
        Returns:
            List of all user entities
        """
        pass
    
    @abstractmethod
    def add(self, user: User) -> User:
        """
        Add a new user
        
        Args:
            user: The user entity to add
            
        Returns:
            The added user with any generated fields
        """
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """
        Update an existing user
        
        Args:
            user: The user entity to update
            
        Returns:
            The updated user
        """
        pass
    
    @abstractmethod
    def delete(self, id: UUID) -> bool:
        """
        Delete a user
        
        Args:
            id: The UUID of the user to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def exists(self, username: str) -> bool:
        """
        Check if a user with the given username exists
        
        Args:
            username: The username to check
            
        Returns:
            True if user exists, False otherwise
        """
        pass
    
    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """
        Check if a user with the given email exists
        
        Args:
            email: The email to check
            
        Returns:
            True if user exists, False otherwise
        """
        pass
    
    @abstractmethod
    def find_by_role(self, role: str) -> List[User]:
        """
        Find users by role
        
        Args:
            role: The role to search for
            
        Returns:
            List of users with the specified role
        """
        pass
    
    @abstractmethod
    def get_next_user_id(self, type_prefix: str) -> str:
        """
        Get the next available user ID for a type
        
        Args:
            type_prefix: The prefix for the user type (INT, EXT, SYS)
            
        Returns:
            Next available user ID
        """
        pass
