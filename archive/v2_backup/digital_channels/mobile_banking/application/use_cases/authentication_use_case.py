"""
Authentication use cases for the Mobile Banking domain.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

from ...domain.entities.mobile_user import MobileBankingUser
from ...domain.entities.mobile_session import MobileBankingSession
from ...domain.services.mobile_authentication_service import MobileAuthenticationService
from ...domain.services.mobile_security_policy_service import MobileSecurityPolicyService
from ..interfaces.mobile_user_repository_interface import MobileUserRepositoryInterface
from ..interfaces.mobile_session_repository_interface import MobileSessionRepositoryInterface
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
    user: Optional[MobileBankingUser] = None
    session: Optional[MobileBankingSession] = None
    token: Optional[str] = None
    additional_auth_required: bool = False


@dataclass
class DeviceRegistrationResult:
    """Result of a device registration attempt."""
    success: bool
    message: str
    device_id: Optional[str] = None


@dataclass
class PasswordChangeResult:
    """Result of a password change attempt."""
    success: bool
    message: str


class AuthenticationUseCase:
    """Use cases related to user authentication."""
    
    def __init__(
        self,
        user_repository: MobileUserRepositoryInterface,
        session_repository: MobileSessionRepositoryInterface,
        notification_service: NotificationServiceInterface,
        audit_log_service: AuditLogServiceInterface,
        auth_service: MobileAuthenticationService,
        security_policy_service: MobileSecurityPolicyService
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
        location: Optional[Dict[str, Any]] = None
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
            return LoginResult(success=False, message="Invalid username or password")
        
        # Verify password
        if not self._auth_service.verify_password(user, password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            self._user_repository.update(user)
            
            # Check if account should be locked
            if self._security_policy_service.should_lock_account(user):
                user.status = "locked"
                user.locked_at = datetime.now()
                self._user_repository.update(user)
                
                self._audit_log_service.log_event(
                    event_type=AuditEventType.ACCOUNT_LOCKED,
                    user_id=user.id,
                    ip_address=ip_address,
                    details={"reason": "Too many failed login attempts"},
                    status="success"
                )
                
                self._notification_service.send_notification(
                    user_id=user.id,
                    notification_type=NotificationType.SECURITY_ALERT,
                    details={
                        "message": "Your account has been locked due to too many failed login attempts. "
                                  "Please contact support to unlock your account."
                    }
                )
                
                return LoginResult(
                    success=False, 
                    message="Your account has been locked due to too many failed login attempts. "
                           "Please contact support to unlock your account."
                )
            
            self._audit_log_service.log_event(
                event_type=AuditEventType.FAILED_LOGIN,
                user_id=user.id,
                ip_address=ip_address,
                details={"reason": "Invalid password", "failed_attempts": user.failed_login_attempts},
                status="failure"
            )
            
            return LoginResult(success=False, message="Invalid username or password")
        
        # Check if account is locked
        if user.status == "locked":
            self._audit_log_service.log_event(
                event_type=AuditEventType.FAILED_LOGIN,
                user_id=user.id,
                ip_address=ip_address,
                details={"reason": "Account locked"},
                status="failure"
            )
            return LoginResult(
                success=False, 
                message="Your account is locked. Please contact support to unlock your account."
            )
        
        # Check device registration
        is_unknown_device = device_id is None or not self._auth_service.is_registered_device(user, device_id)
        needs_additional_auth = is_unknown_device and self._security_policy_service.requires_additional_auth_for_new_device(user)
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        self._user_repository.update(user)
        
        # Create session
        session = MobileBankingSession(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            start_time=datetime.now(),
            is_active=True,
            location=location
        )
        
        # Generate token
        token = self._auth_service.generate_session_token()
        session.token = token
        
        # Save session
        session = self._session_repository.save(session)
        
        # Log successful login
        self._audit_log_service.log_event(
            event_type=AuditEventType.LOGIN,
            user_id=user.id,
            ip_address=ip_address,
            details={
                "device_id": device_id,
                "is_unknown_device": is_unknown_device,
                "requires_additional_auth": needs_additional_auth
            },
            status="success",
            device_info={"user_agent": user_agent},
            location=location
        )
        
        # Send notification
        self._notification_service.send_notification(
            user_id=user.id,
            notification_type=NotificationType.LOGIN_SUCCESS if not is_unknown_device 
                             else NotificationType.NEW_DEVICE_LOGIN,
            details={
                "time": datetime.now().isoformat(),
                "ip_address": ip_address,
                "device": user_agent
            }
        )
        
        return LoginResult(
            success=True,
            message="Login successful" if not needs_additional_auth else "Additional authentication required",
            user=user,
            session=session,
            token=token,
            additional_auth_required=needs_additional_auth
        )
    
    def register_device(
        self,
        user_id: UUID,
        device_id: str,
        device_name: str,
        device_model: str,
        os_version: str,
        app_version: str,
        ip_address: str
    ) -> DeviceRegistrationResult:
        """
        Register a device for a user.
        
        Args:
            user_id: The ID of the user
            device_id: The unique identifier for the device
            device_name: The name of the device
            device_model: The model of the device
            os_version: The OS version of the device
            app_version: The app version installed on the device
            ip_address: The IP address of the request
            
        Returns:
            DeviceRegistrationResult with result information
        """
        # Find the user
        user = self._user_repository.get_by_id(user_id)
        
        if user is None:
            return DeviceRegistrationResult(success=False, message="User not found")
        
        # Check if device is already registered
        if self._auth_service.is_registered_device(user, device_id):
            return DeviceRegistrationResult(
                success=True, 
                message="Device already registered",
                device_id=device_id
            )
        
        # Register the device
        success = self._auth_service.register_device(
            user=user,
            device_id=device_id,
            device_name=device_name,
            device_model=device_model,
            os_version=os_version,
            app_version=app_version
        )
        
        if not success:
            return DeviceRegistrationResult(success=False, message="Failed to register device")
        
        # Save the updated user
        self._user_repository.update(user)
        
        # Log the device registration
        self._audit_log_service.log_event(
            event_type=AuditEventType.DEVICE_REGISTRATION,
            user_id=user.id,
            ip_address=ip_address,
            details={
                "device_id": device_id,
                "device_name": device_name,
                "device_model": device_model
            },
            status="success"
        )
        
        # Send notification
        self._notification_service.send_notification(
            user_id=user.id,
            notification_type=NotificationType.SECURITY_ALERT,
            details={
                "message": f"New device registered: {device_name}",
                "time": datetime.now().isoformat()
            }
        )
        
        return DeviceRegistrationResult(
            success=True,
            message="Device registered successfully",
            device_id=device_id
        )
    
    def logout(self, token: str, ip_address: str) -> bool:
        """
        Log out a user by invalidating their session.
        
        Args:
            token: The session token
            ip_address: The IP address of the request
            
        Returns:
            True if logout was successful, False otherwise
        """
        # Find the session
        session = self._session_repository.get_by_token(token)
        
        if session is None or not session.is_active:
            return False
        
        # Invalidate the session
        session.is_active = False
        session.end_time = datetime.now()
        self._session_repository.update(session)
        
        # Log the logout
        self._audit_log_service.log_event(
            event_type=AuditEventType.LOGOUT,
            user_id=session.user_id,
            ip_address=ip_address,
            details={"session_id": str(session.id)},
            status="success"
        )
        
        return True
    
    def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
        ip_address: str
    ) -> PasswordChangeResult:
        """
        Change a user's password.
        
        Args:
            user_id: The ID of the user
            current_password: The user's current password
            new_password: The user's new password
            ip_address: The IP address of the request
            
        Returns:
            PasswordChangeResult with result information
        """
        # Find the user
        user = self._user_repository.get_by_id(user_id)
        
        if user is None:
            return PasswordChangeResult(success=False, message="User not found")
        
        # Verify current password
        if not self._auth_service.verify_password(user, current_password):
            self._audit_log_service.log_event(
                event_type=AuditEventType.PASSWORD_CHANGE,
                user_id=user.id,
                ip_address=ip_address,
                details={"reason": "Current password verification failed"},
                status="failure"
            )
            return PasswordChangeResult(success=False, message="Current password is incorrect")
        
        # Check if new password meets security requirements
        if not self._security_policy_service.validate_password_strength(new_password):
            return PasswordChangeResult(
                success=False, 
                message="New password does not meet security requirements"
            )
        
        # Check if new password is same as old password
        if self._auth_service.verify_password(user, new_password):
            return PasswordChangeResult(
                success=False, 
                message="New password must be different from current password"
            )
        
        # Update password
        self._auth_service.update_password(user, new_password)
        self._user_repository.update(user)
        
        # Log password change
        self._audit_log_service.log_event(
            event_type=AuditEventType.PASSWORD_CHANGE,
            user_id=user.id,
            ip_address=ip_address,
            details={},
            status="success"
        )
        
        # Send notification
        self._notification_service.send_notification(
            user_id=user.id,
            notification_type=NotificationType.PASSWORD_CHANGE,
            details={
                "time": datetime.now().isoformat()
            }
        )
        
        return PasswordChangeResult(success=True, message="Password changed successfully")
