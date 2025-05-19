"""
Mobile Session repository interface for the Mobile Banking domain.
This interface defines methods for persisting and retrieving mobile banking sessions.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ...domain.entities.mobile_session import MobileBankingSession

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class MobileSessionRepositoryInterface(ABC):
    """Interface for mobile session repository operations."""
    
    @abstractmethod
    def get_by_id(self, session_id: UUID) -> Optional[MobileBankingSession]:
        """
        Get a session by its ID.
        
        Args:
            session_id: The ID of the session to get
            
        Returns:
            MobileBankingSession if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_token(self, token: str) -> Optional[MobileBankingSession]:
        """
        Get a session by its token.
        
        Args:
            token: The token of the session to get
            
        Returns:
            MobileBankingSession if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_active_sessions_by_user_id(self, user_id: UUID) -> List[MobileBankingSession]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of active MobileBankingSession objects
        """
        pass
    
    @abstractmethod
    def save(self, session: MobileBankingSession) -> MobileBankingSession:
        """
        Save a session to the repository.
        
        Args:
            session: The session to save
            
        Returns:
            The saved session with any updates (e.g., ID assignment)
        """
        pass
    
    @abstractmethod
    def update(self, session: MobileBankingSession) -> MobileBankingSession:
        """
        Update an existing session.
        
        Args:
            session: The session to update
            
        Returns:
            The updated session
        """
        pass
    
    @abstractmethod
    def delete(self, session_id: UUID) -> bool:
        """
        Delete a session by its ID.
        
        Args:
            session_id: The ID of the session to delete
            
        Returns:
            True if session was deleted, False otherwise
        """
        pass
