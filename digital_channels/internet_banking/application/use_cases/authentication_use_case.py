"""
Authentication use cases for the Internet Banking domain.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

from ...domain.entities.user import InternetBankingUser
from ...domain.entities.session import InternetBankingSession
from ...domain.services.authentication_service import AuthenticationService
from ...domain.services.security_policy_service import SecurityPolicyService
from ..interfaces.user_repository_interface import UserRepositoryInterface
from ..interfaces.session_repository_interface import SessionRepositoryInterface
from ..interfaces.notification_service_interface import NotificationServiceInterface, NotificationType
from ..interfaces.audit_log_service_interface import AuditLogServiceInterface, AuditEventType

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



@dataclass
class LoginResult:
    """Result of a login attempt."""
    success: bool
    message: str
    user: Optional[InternetBankingUser] = None
    session: Optional[InternetBankingSession] = None
    token: Optional[str] = None
    additional_auth_required: bool = False


@dataclass
class PasswordChangeResult:
    """Result of a password change attempt."""
    success: bool
    message: str


class AuthenticationUseCase:
    """Use cases related to user authentication."""
    
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        session_repository: SessionRepositoryInterface,
        notification_service: NotificationServiceInterface,
        audit_log_service: AuditLogServiceInterface,
        auth_service: AuthenticationService,
        security_policy_service: SecurityPolicyService
    ):
        """
        Initialize the authentication use case.
        
        Args:
            user_repository: Repository for user operations
            session_repository: Repository for session operations
            notification_service: Service for sending notifications
            audit_log_service: Service for logging audit events
            auth_service: Domain service for authentication
            security_policy_service: Domain service for security policies
        """
        self._user_repository = user_repository
        self._session_repository = session_repository
        self._notification_service = notification_service
        self._audit_log_service = audit_log_service
        self._auth_service = auth_service
        self._security_policy_service = security_policy_service
    
    def login(
        self, 
        username: str, 
        password: str,
        ip_address: str,
        user_agent: str,
        device_id: Optional[str] = None,
        location: Optional[str] = None
    ) -> LoginResult:
        """
        Authenticate a user and create a session.
        
        Args:
            username: User's username
            password: User's password
            ip_address: Client IP address
            user_agent: Client user agent
            device_id: Optional device identifier
            location: Optional location information
            
        Returns:
            LoginResult with result information
        """
        # Find the user
        user = self._user_repository.get_by_username(username)
        
        # User not found
        if user is None:
            self._audit_log_service.log_event(
                event_type=AuditEventType.FAILED_LOGIN,
                user_id=None,
                ip_address=ip_address,
                details={"reason": "User not found", "username": username},
                status="failure"
            )
            return LoginResult(
                success=False,
                message="Invalid username or password"
            )
        
        # Verify password
        if not self._auth_service.verify_password(user, password):
            user.record_login(False, device_id)
            self._user_repository.save(user)
            
            self._audit_log_service.log_event(
                event_type=AuditEventType.FAILED_LOGIN,
                user_id=user.user_id,
                ip_address=ip_address,
                details={"reason": "Invalid password"},
                status="failure"
            )
            
            return LoginResult(
                success=False,
                message="Invalid username or password"
            )
        
        # Check if user is allowed to login
        if not self._auth_service.can_login(user):
            self._audit_log_service.log_event(
                event_type=AuditEventType.FAILED_LOGIN,
                user_id=user.user_id,
                ip_address=ip_address,
                details={"reason": f"Account status: {user.status.value}"},
                status="failure"
            )
            
            return LoginResult(
                success=False,
                message=f"Login not allowed. Account status: {user.status.value}"
            )
        
        # Record successful login
        user.record_login(True, device_id)
        self._user_repository.save(user)
        
        # Get known devices and locations for this user
        known_devices = user.registered_devices
        # In a real implementation, we would have a way to get known locations
        known_locations = [] if location is None else [location]
        
        # Check for suspicious activity
        is_suspicious, reason = self._security_policy_service.detect_suspicious_activity(
            user, 
            InternetBankingSession.create(
                user_id=user.user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_id=device_id
            ),
            known_devices, 
            known_locations
        )
        
        # Create a session
        session = InternetBankingSession.create(
            user_id=user.user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id
        )
        
        if location:
            session.update_location(location)
        
        session = self._session_repository.save(session)
        
        # Generate a simple token (in production, use a JWT or similar)
        token = f"{session.session_id}_{datetime.now().timestamp()}"
        
        # Log successful login
        self._audit_log_service.log_event(
            event_type=AuditEventType.USER_LOGIN,
            user_id=user.user_id,
            session_id=session.session_id,
            ip_address=ip_address,
            details={"user_agent": user_agent, "device_id": device_id},
            status="success"
        )
        
        # Send login notification
        self._notification_service.send_email(
            to_email=user.email,
            subject="New login to your account",
            message=f"A new login to your account was detected from {ip_address} at {datetime.now()}",
            notification_type=NotificationType.LOGIN_ALERT
        )
        
        return LoginResult(
            success=True,
            message="Login successful",
            user=user,
            session=session,
            token=token,
            additional_auth_required=is_suspicious
        )
    
    def logout(self, session_id: UUID, user_id: UUID, ip_address: str) -> bool:
        """
        Log out a user by terminating their session.
        
        Args:
            session_id: ID of the session to terminate
            user_id: ID of the user
            ip_address: Client IP address
            
        Returns:
            Boolean indicating if the logout was successful
        """
        # Get the session
        session = self._session_repository.get_by_id(session_id)
        
        # Session not found or doesn't belong to the user
        if session is None or session.user_id != user_id:
            return False
        
        # Terminate the session
        session.terminate()
        self._session_repository.save(session)
        
        # Log the logout
        self._audit_log_service.log_event(
            event_type=AuditEventType.USER_LOGOUT,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            status="success"
        )
        
        return True
    
    def change_password(
        self, 
        user_id: UUID,
        old_password: str,
        new_password: str,
        session_id: UUID,
        ip_address: str
    ) -> PasswordChangeResult:
        """
        Change a user's password.
        
        Args:
            user_id: ID of the user
            old_password: User's current password
            new_password: User's new password
            session_id: ID of the current session
            ip_address: Client IP address
            
        Returns:
            PasswordChangeResult with result information
        """
        # Find the user
        user = self._user_repository.get_by_id(user_id)
        
        # User not found
        if user is None:
            return PasswordChangeResult(
                success=False,
                message="User not found"
            )
        
        # Verify current password
        if not self._auth_service.verify_password(user, old_password):
            return PasswordChangeResult(
                success=False,
                message="Current password is incorrect"
            )
        
        # Check if new password meets security requirements
        is_secure, reason = self._security_policy_service.is_secure_password(new_password)
        if not is_secure:
            return PasswordChangeResult(
                success=False,
                message=f"Password does not meet security requirements: {reason}"
            )
        
        # Hash the new password
        password_hash, salt = self._auth_service.generate_password_hash(new_password)
        
        # Update the user's password
        user.change_password(password_hash, salt)
        self._user_repository.save(user)
        
        # Log the password change
        self._audit_log_service.log_event(
            event_type=AuditEventType.PASSWORD_CHANGE,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            status="success"
        )
        
        # Send password change notification
        self._notification_service.send_email(
            to_email=user.email,
            subject="Your password has been changed",
            message=f"Your password was changed at {datetime.now()}. If you did not make this change, please contact support immediately.",
            notification_type=NotificationType.SECURITY_ALERT
        )
        
        return PasswordChangeResult(
            success=True,
            message="Password changed successfully"
        )
