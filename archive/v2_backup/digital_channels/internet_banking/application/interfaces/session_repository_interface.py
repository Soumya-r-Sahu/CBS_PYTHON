"""
Session repository interface for the Internet Banking domain.
This interface defines methods for persisting and retrieving sessions.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ...domain.entities.session import InternetBankingSession

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class SessionRepositoryInterface(ABC):
    """Interface for session repository operations."""
    
    @abstractmethod
    def get_by_id(self, session_id: UUID) -> Optional[InternetBankingSession]:
        """
        Get a session by its ID.
        
        Args:
            session_id: The ID of the session to get
            
        Returns:
            InternetBankingSession if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_active_session_by_user_id(self, user_id: UUID) -> Optional[InternetBankingSession]:
        """
        Get the active session for a user, if any.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Active InternetBankingSession if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_token(self, token: str) -> Optional[InternetBankingSession]:
        """
        Get a session by its authentication token.
        
        Args:
            token: The authentication token
            
        Returns:
            InternetBankingSession if found, None otherwise
        """
        pass
    
    @abstractmethod
    def save(self, session: InternetBankingSession) -> InternetBankingSession:
        """
        Save or update a session.
        
        Args:
            session: The session to save
            
        Returns:
            The saved session (with any generated IDs if it's a new session)
        """
        pass
    
    @abstractmethod
    def delete(self, session_id: UUID) -> bool:
        """
        Delete a session by its ID.
        
        Args:
            session_id: The ID of the session to delete
            
        Returns:
            True if the session was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def list_active_sessions(self) -> List[InternetBankingSession]:
        """
        Get a list of all active sessions.
        
        Returns:
            List of active InternetBankingSession objects
        """
        pass
    
    @abstractmethod
    def list_sessions_by_user_id(self, user_id: UUID) -> List[InternetBankingSession]:
        """
        Get all sessions for a specific user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of InternetBankingSession objects for the user
        """
        pass
    
    @abstractmethod
    def terminate_all_sessions_for_user(self, user_id: UUID) -> int:
        """
        Terminate all active sessions for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Number of sessions terminated
        """
        pass
