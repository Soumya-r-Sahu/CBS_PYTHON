"""
Session management use cases for the Internet Banking domain.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from ...domain.entities.session import InternetBankingSession, SessionStatus
from ...domain.services.authentication_service import AuthenticationService
from ..interfaces.session_repository_interface import SessionRepositoryInterface
from ..interfaces.audit_log_service_interface import AuditLogServiceInterface, AuditEventType

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



@dataclass
class SessionValidationResult:
    """Result of a session validation attempt."""
    valid: bool
    message: str
    session: Optional[InternetBankingSession] = None


class SessionManagementUseCase:
    """Use cases related to session management."""
    
    def __init__(
        self,
        session_repository: SessionRepositoryInterface,
        audit_log_service: AuditLogServiceInterface,
        auth_service: AuthenticationService
    ):
        """
        Initialize the session management use case.
        
        Args:
            session_repository: Repository for session operations
            audit_log_service: Service for logging audit events
            auth_service: Domain service for authentication
        """
        self._session_repository = session_repository
        self._audit_log_service = audit_log_service
        self._auth_service = auth_service
    
    def validate_session(self, session_id: UUID, token: str) -> SessionValidationResult:
        """
        Validate a session.
        
        Args:
            session_id: ID of the session to validate
            token: Authentication token
            
        Returns:
            SessionValidationResult with result information
        """
        # Get the session
        session = self._session_repository.get_by_id(session_id)
        
        # Session not found
        if session is None:
            return SessionValidationResult(
                valid=False,
                message="Session not found"
            )
        
        # Check if the session is valid
        if not self._auth_service.is_session_valid(session):
            return SessionValidationResult(
                valid=False,
                message="Session is not valid or has expired"
            )
        
        # In a real implementation, validate the token against the session
        # For this example, we'll just check if the token contains the session ID
        if str(session_id) not in token:
            return SessionValidationResult(
                valid=False,
                message="Invalid token"
            )
        
        # Session is valid
        return SessionValidationResult(
            valid=True,
            message="Session is valid",
            session=session
        )
    
    def refresh_session(self, session_id: UUID, token: str) -> SessionValidationResult:
        """
        Refresh a session to extend its expiration.
        
        Args:
            session_id: ID of the session to refresh
            token: Authentication token
            
        Returns:
            SessionValidationResult with result information
        """
        # Validate the session first
        validation_result = self.validate_session(session_id, token)
        
        # Session is not valid
        if not validation_result.valid:
            return validation_result
        
        # Session is valid, refresh it
        session = validation_result.session
        session.update_activity()
        updated_session = self._session_repository.save(session)
        
        return SessionValidationResult(
            valid=True,
            message="Session refreshed",
            session=updated_session
        )
    
    def terminate_session(self, session_id: UUID, user_id: UUID, ip_address: str) -> bool:
        """
        Terminate a session.
        
        Args:
            session_id: ID of the session to terminate
            user_id: ID of the user
            ip_address: IP address of the client
            
        Returns:
            Boolean indicating if the session was terminated successfully
        """
        # Get the session
        session = self._session_repository.get_by_id(session_id)
        
        # Session not found or doesn't belong to the user
        if session is None or session.user_id != user_id:
            return False
        
        # Terminate the session
        session.terminate()
        self._session_repository.save(session)
        
        # Log the termination
        self._audit_log_service.log_event(
            event_type=AuditEventType.USER_LOGOUT,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            details={"reason": "Session terminated"},
            status="success"
        )
        
        return True
    
    def terminate_all_user_sessions(self, user_id: UUID, ip_address: str) -> int:
        """
        Terminate all sessions for a user.
        
        Args:
            user_id: ID of the user
            ip_address: IP address of the client
            
        Returns:
            Number of sessions terminated
        """
        # Terminate all sessions for the user
        count = self._session_repository.terminate_all_sessions_for_user(user_id)
        
        # Log the termination if any sessions were terminated
        if count > 0:
            self._audit_log_service.log_event(
                event_type=AuditEventType.USER_LOGOUT,
                user_id=user_id,
                ip_address=ip_address,
                details={"reason": "All sessions terminated", "count": count},
                status="success"
            )
        
        return count
    
    def list_active_sessions(self, user_id: UUID) -> List[InternetBankingSession]:
        """
        Get a list of active sessions for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of active sessions for the user
        """
        # Get all sessions for the user
        all_sessions = self._session_repository.list_sessions_by_user_id(user_id)
        
        # Filter to active sessions
        return [session for session in all_sessions if session.status == SessionStatus.ACTIVE]
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        # Get all active sessions
        active_sessions = self._session_repository.list_active_sessions()
        
        # Identify expired sessions
        expired_count = 0
        for session in active_sessions:
            if not self._auth_service.is_session_valid(session):
                session.expire()
                self._session_repository.save(session)
                expired_count += 1
        
        return expired_count
