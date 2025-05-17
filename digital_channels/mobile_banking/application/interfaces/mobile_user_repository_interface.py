"""
Mobile User repository interface for the Mobile Banking domain.
This interface defines methods for persisting and retrieving mobile banking users.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ...domain.entities.mobile_user import MobileBankingUser


class MobileUserRepositoryInterface(ABC):
    """Interface for mobile user repository operations."""
    
    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[MobileBankingUser]:
        """
        Get a user by their ID.
        
        Args:
            user_id: The ID of the user to get
            
        Returns:
            MobileBankingUser if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[MobileBankingUser]:
        """
        Get a user by their username.
        
        Args:
            username: The username of the user to get
            
        Returns:
            MobileBankingUser if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_mobile_number(self, mobile_number: str) -> Optional[MobileBankingUser]:
        """
        Get a user by their registered mobile number.
        
        Args:
            mobile_number: The mobile number of the user to get
            
        Returns:
            MobileBankingUser if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_customer_id(self, customer_id: str) -> Optional[MobileBankingUser]:
        """
        Get a user by their customer ID.
        
        Args:
            customer_id: The customer ID of the user to get
            
        Returns:
            MobileBankingUser if found, None otherwise
        """
        pass
    
    @abstractmethod
    def save(self, user: MobileBankingUser) -> MobileBankingUser:
        """
        Save a user to the repository.
        
        Args:
            user: The user to save
            
        Returns:
            The saved user with any updates (e.g., ID assignment)
        """
        pass
    
    @abstractmethod
    def update(self, user: MobileBankingUser) -> MobileBankingUser:
        """
        Update an existing user.
        
        Args:
            user: The user to update
            
        Returns:
            The updated user
        """
        pass
    
    @abstractmethod
    def delete(self, user_id: UUID) -> bool:
        """
        Delete a user by their ID.
        
        Args:
            user_id: The ID of the user to delete
            
        Returns:
            True if user was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[MobileBankingUser]:
        """
        Get all users.
        
        Returns:
            A list of all users
        """
        pass
