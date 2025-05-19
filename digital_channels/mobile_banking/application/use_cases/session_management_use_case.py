"""
Session management use cases for the Mobile Banking domain.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

from ...domain.entities.mobile_session import MobileBankingSession
from ...domain.services.mobile_security_policy_service import MobileSecurityPolicyService
from ..interfaces.mobile_session_repository_interface import MobileSessionRepositoryInterface
from ..interfaces.mobile_user_repository_interface import MobileUserRepositoryInterface
from ..interfaces.audit_log_service_interface import AuditLogServiceInterface, AuditEventType

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



@dataclass
class SessionValidationResult:
    """Result of a session validation."""
    is_valid: bool
    message: str
    session: Optional[MobileBankingSession] = None
    needs_extension: bool = False


class SessionManagementUseCase:
    """Use cases related to session management."""
    
    def __init__(
        self,
        session_repository: MobileSessionRepositoryInterface,
        user_repository: MobileUserRepositoryInterface,
        audit_log_service: AuditLogServiceInterface,
        security_policy_service: MobileSecurityPolicyService
    ):
        """
        Initialize the session management use case.
        
        Args:
            session_repository: Repository for session operations
            user_repository: Repository for user operations
            audit_log_service: Service for logging audit events
            security_policy_service: Domain service for security policies
        """
        self._session_repository = session_repository
        self._user_repository = user_repository
        self._audit_log_service = audit_log_service
        self._security_policy_service = security_policy_service
    
    def validate_session(
        self,
        token: str,
        ip_address: str,
        user_agent: str,
        device_id: Optional[str] = None
    ) -> SessionValidationResult:
        """
        Validate a session.
        
        Args:
            token: The session token to validate
            ip_address: The IP address of the request
            user_agent: The user agent of the request
            device_id: The device ID of the request
            
        Returns:
            SessionValidationResult with validation information
        """
        # Find the session
        session = self._session_repository.get_by_token(token)
        
        # Session not found or inactive
        if session is None or not session.is_active:
            return SessionValidationResult(
                is_valid=False,
                message="Invalid or expired session"
            )
        
        # Get the user
        user = self._user_repository.get_by_id(session.user_id)
        if user is None:
            return SessionValidationResult(
                is_valid=False,
                message="User not found"
            )
        
        # Check if session is expired
        if self._security_policy_service.is_session_expired(session):
            # Invalidate the session
            session.is_active = False
            session.end_time = datetime.now()
            self._session_repository.update(session)
            
            # Log session expiration
            self._audit_log_service.log_event(
                event_type=AuditEventType.SESSION_EXPIRED,
                user_id=session.user_id,
                ip_address=ip_address,
                details={"session_id": str(session.id)},
                status="success"
            )
            
            return SessionValidationResult(
                is_valid=False,
                message="Session expired"
            )
        
        # Check if IP address has changed (potential session hijacking)
        if self._security_policy_service.enforce_ip_binding() and session.ip_address != ip_address:
            # Invalidate the session
            session.is_active = False
            session.end_time = datetime.now()
            self._session_repository.update(session)
            
            # Log potential session hijacking attempt
            self._audit_log_service.log_event(
                event_type=AuditEventType.SECURITY_SETTING_CHANGE,
                user_id=session.user_id,
                ip_address=ip_address,
                details={
                    "reason": "IP address change",
                    "original_ip": session.ip_address,
                    "new_ip": ip_address
                },
                status="failure"
            )
            
            return SessionValidationResult(
                is_valid=False,
                message="Session invalid due to IP address change"
            )
        
        # Check if device ID has changed
        if (device_id is not None and session.device_id is not None and 
            self._security_policy_service.enforce_device_binding() and 
            session.device_id != device_id):
            
            # Invalidate the session
            session.is_active = False
            session.end_time = datetime.now()
            self._session_repository.update(session)
            
            # Log potential session hijacking attempt
            self._audit_log_service.log_event(
                event_type=AuditEventType.SECURITY_SETTING_CHANGE,
                user_id=session.user_id,
                ip_address=ip_address,
                details={
                    "reason": "Device ID change",
                    "original_device_id": session.device_id,
                    "new_device_id": device_id
                },
                status="failure"
            )
            
            return SessionValidationResult(
                is_valid=False,
                message="Session invalid due to device change"
            )
        
        # Check if session needs extension
        needs_extension = self._security_policy_service.session_needs_extension(session)
        
        return SessionValidationResult(
            is_valid=True,
            message="Session valid",
            session=session,
            needs_extension=needs_extension
        )
    
    def extend_session(self, token: str, ip_address: str) -> bool:
        """
        Extend a session's validity period.
        
        Args:
            token: The session token to extend
            ip_address: The IP address of the request
            
        Returns:
            True if session was extended, False otherwise
        """
        # Find the session
        session = self._session_repository.get_by_token(token)
        
        # Session not found or inactive
        if session is None or not session.is_active:
            return False
        
        # Extend the session
        session.last_activity_time = datetime.now()
        self._session_repository.update(session)
        
        # Log session extension
        self._audit_log_service.log_event(
            event_type=AuditEventType.SESSION_EXTENDED,
            user_id=session.user_id,
            ip_address=ip_address,
            details={"session_id": str(session.id)},
            status="success"
        )
        
        return True
    
    def invalidate_all_user_sessions(self, user_id: UUID, ip_address: str) -> int:
        """
        Invalidate all active sessions for a user.
        
        Args:
            user_id: The ID of the user
            ip_address: The IP address of the request
            
        Returns:
            Number of sessions invalidated
        """
        # Find all active sessions for the user
        sessions = self._session_repository.get_active_sessions_by_user_id(user_id)
        
        # Invalidate all sessions
        count = 0
        for session in sessions:
            session.is_active = False
            session.end_time = datetime.now()
            self._session_repository.update(session)
            count += 1
        
        # Log invalidation
        if count > 0:
            self._audit_log_service.log_event(
                event_type=AuditEventType.SECURITY_SETTING_CHANGE,
                user_id=user_id,
                ip_address=ip_address,
                details={"invalidated_sessions_count": count},
                status="success"
            )
        
        return count
    
    def get_active_sessions(self, user_id: UUID) -> List[MobileBankingSession]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of active sessions
        """
        return self._session_repository.get_active_sessions_by_user_id(user_id)
