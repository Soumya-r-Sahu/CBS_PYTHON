"""
User repository interface for the Internet Banking domain.
This interface defines methods for persisting and retrieving users.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ...domain.entities.user import InternetBankingUser

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class UserRepositoryInterface(ABC):
    """Interface for user repository operations."""
    
    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[InternetBankingUser]:
        """
        Get a user by their ID.
        
        Args:
            user_id: The ID of the user to get
            
        Returns:
            InternetBankingUser if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[InternetBankingUser]:
        """
        Get a user by their username.
        
        Args:
            username: The username to search for
            
        Returns:
            InternetBankingUser if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_customer_id(self, customer_id: UUID) -> Optional[InternetBankingUser]:
        """
        Get a user by their associated customer ID.
        
        Args:
            customer_id: The customer ID to search for
            
        Returns:
            InternetBankingUser if found, None otherwise
        """
        pass
    
    @abstractmethod
    def save(self, user: InternetBankingUser) -> InternetBankingUser:
        """
        Save or update a user.
        
        Args:
            user: The user to save
            
        Returns:
            The saved user (with any generated IDs if it's a new user)
        """
        pass
    
    @abstractmethod
    def delete(self, user_id: UUID) -> bool:
        """
        Delete a user by their ID.
        
        Args:
            user_id: The ID of the user to delete
            
        Returns:
            True if the user was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def list_active_users(self) -> List[InternetBankingUser]:
        """
        Get a list of all active users.
        
        Returns:
            List of active InternetBankingUser objects
        """
        pass
