"""
User management use cases for the Mobile Banking domain.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from ...domain.entities.mobile_user import MobileBankingUser, RegisteredDevice
from ...domain.services.mobile_authentication_service import MobileAuthenticationService
from ...domain.services.mobile_security_policy_service import MobileSecurityPolicyService
from ..interfaces.mobile_user_repository_interface import MobileUserRepositoryInterface
from ..interfaces.notification_service_interface import NotificationServiceInterface, NotificationType
from ..interfaces.audit_log_service_interface import AuditLogServiceInterface, AuditEventType


@dataclass
class UserRegistrationResult:
    """Result of a user registration attempt."""
    success: bool
    message: str
    user: Optional[MobileBankingUser] = None


@dataclass
class ProfileUpdateResult:
    """Result of a profile update attempt."""
    success: bool
    message: str
    user: Optional[MobileBankingUser] = None


class UserManagementUseCase:
    """Use cases related to user management."""
    
    def __init__(
        self,
        user_repository: MobileUserRepositoryInterface,
        notification_service: NotificationServiceInterface,
        audit_log_service: AuditLogServiceInterface,
        auth_service: MobileAuthenticationService,
        security_policy_service: MobileSecurityPolicyService
    ):
        """
        Initialize the user management use case.
        
        Args:
            user_repository: Repository for user operations
            notification_service: Service for sending notifications
            audit_log_service: Service for logging audit events
            auth_service: Domain service for authentication
            security_policy_service: Domain service for security policies
        """
        self._user_repository = user_repository
        self._notification_service = notification_service
        self._audit_log_service = audit_log_service
        self._auth_service = auth_service
        self._security_policy_service = security_policy_service
    
    def register_user(
        self,
        username: str,
        password: str,
        mobile_number: str,
        email: str,
        full_name: str,
        customer_id: str,
        ip_address: str,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None
    ) -> UserRegistrationResult:
        """
        Register a new mobile banking user.
        
        Args:
            username: The username for the new user
            password: The password for the new user
            mobile_number: The mobile number of the user
            email: The email address of the user
            full_name: The full name of the user
            customer_id: The customer ID of the user
            ip_address: The IP address of the request
            device_id: Optional device identifier
            device_info: Optional device information
            
        Returns:
            UserRegistrationResult with result information
        """
        # Check if username already exists
        existing_user = self._user_repository.get_by_username(username)
        if existing_user is not None:
            return UserRegistrationResult(
                success=False,
                message="Username already exists"
            )
        
        # Check if mobile number already registered
        existing_user = self._user_repository.get_by_mobile_number(mobile_number)
        if existing_user is not None:
            return UserRegistrationResult(
                success=False,
                message="Mobile number already registered"
            )
        
        # Check if customer ID already registered
        existing_user = self._user_repository.get_by_customer_id(customer_id)
        if existing_user is not None:
            return UserRegistrationResult(
                success=False,
                message="Customer ID already registered"
            )
        
        # Validate password strength
        if not self._security_policy_service.validate_password_strength(password):
            return UserRegistrationResult(
                success=False,
                message="Password does not meet security requirements"
            )
        
        # Create user
        user = MobileBankingUser(
            username=username,
            mobile_number=mobile_number,
            email=email,
            full_name=full_name,
            customer_id=customer_id,
            status="active",
            profile_complete=True,
            registration_date=datetime.now(),
            registered_devices=[]
        )
        
        # Set password hash
        user.credentials = self._auth_service.create_credentials(password)
        
        # Register device if provided
        if device_id is not None and device_info is not None:
            device = RegisteredDevice(
                device_id=device_id,
                device_name=device_info.get('device_name', 'Unknown'),
                device_model=device_info.get('device_model', 'Unknown'),
                os_version=device_info.get('os_version', 'Unknown'),
                app_version=device_info.get('app_version', 'Unknown'),
                registration_date=datetime.now(),
                last_used_date=datetime.now()
            )
            user.registered_devices.append(device)
        
        # Save user
        user = self._user_repository.save(user)
        
        # Log registration
        self._audit_log_service.log_event(
            event_type=AuditEventType.PROFILE_UPDATE,
            user_id=user.id,
            ip_address=ip_address,
            details={"action": "user_registration"},
            status="success",
            device_info=device_info
        )
        
        # Send welcome notification
        self._notification_service.send_notification(
            user_id=user.id,
            notification_type=NotificationType.SECURITY_ALERT,
            details={
                "message": "Welcome to Mobile Banking! Your account has been successfully registered.",
                "time": datetime.now().isoformat()
            }
        )
        
        return UserRegistrationResult(
            success=True,
            message="User registered successfully",
            user=user
        )
    
    def update_profile(
        self,
        user_id: UUID,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        ip_address: str = None
    ) -> ProfileUpdateResult:
        """
        Update a user's profile.
        
        Args:
            user_id: The ID of the user
            email: Optional new email address
            full_name: Optional new full name
            preferences: Optional user preferences
            ip_address: The IP address of the request
            
        Returns:
            ProfileUpdateResult with result information
        """
        # Get the user
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            return ProfileUpdateResult(
                success=False,
                message="User not found"
            )
        
        # Update fields if provided
        updated = False
        update_details = {}
        
        if email is not None and email != user.email:
            user.email = email
            updated = True
            update_details["email"] = email
        
        if full_name is not None and full_name != user.full_name:
            user.full_name = full_name
            updated = True
            update_details["full_name"] = full_name
        
        if preferences is not None:
            # Update only the provided preferences, not the entire dict
            user.preferences = {**(user.preferences or {}), **preferences}
            updated = True
            update_details["preferences"] = preferences
        
        # If nothing was updated
        if not updated:
            return ProfileUpdateResult(
                success=True,
                message="No changes to update",
                user=user
            )
        
        # Save changes
        user = self._user_repository.update(user)
        
        # Log profile update
        self._audit_log_service.log_event(
            event_type=AuditEventType.PROFILE_UPDATE,
            user_id=user.id,
            ip_address=ip_address,
            details={"updated_fields": update_details},
            status="success"
        )
        
        return ProfileUpdateResult(
            success=True,
            message="Profile updated successfully",
            user=user
        )
    
    def update_mobile_number(
        self,
        user_id: UUID,
        new_mobile_number: str,
        verification_code: str,
        ip_address: str
    ) -> ProfileUpdateResult:
        """
        Update a user's mobile number with verification.
        
        Args:
            user_id: The ID of the user
            new_mobile_number: The new mobile number
            verification_code: Verification code sent to the new number
            ip_address: The IP address of the request
            
        Returns:
            ProfileUpdateResult with result information
        """
        # Get the user
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            return ProfileUpdateResult(
                success=False,
                message="User not found"
            )
        
        # Check if mobile number already registered
        existing_user = self._user_repository.get_by_mobile_number(new_mobile_number)
        if existing_user is not None and existing_user.id != user_id:
            return ProfileUpdateResult(
                success=False,
                message="Mobile number already registered to another user"
            )
        
        # Verify the verification code (in real implementation, would call a verification service)
        # This is a placeholder check
        if not self._security_policy_service.verify_mobile_number_change_code(verification_code):
            return ProfileUpdateResult(
                success=False,
                message="Invalid verification code"
            )
        
        # Update mobile number
        old_mobile_number = user.mobile_number
        user.mobile_number = new_mobile_number
        user = self._user_repository.update(user)
        
        # Log mobile number update
        self._audit_log_service.log_event(
            event_type=AuditEventType.PROFILE_UPDATE,
            user_id=user.id,
            ip_address=ip_address,
            details={
                "field": "mobile_number",
                "old_value": old_mobile_number,
                "new_value": new_mobile_number
            },
            status="success"
        )
        
        # Send notifications to both old and new numbers
        self._notification_service.send_notification(
            user_id=user.id,
            notification_type=NotificationType.SECURITY_ALERT,
            details={
                "message": "Your mobile number has been updated.",
                "time": datetime.now().isoformat()
            }
        )
        
        return ProfileUpdateResult(
            success=True,
            message="Mobile number updated successfully",
            user=user
        )
    
    def get_user_by_id(self, user_id: UUID) -> Optional[MobileBankingUser]:
        """
        Get a user by their ID.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            MobileBankingUser if found, None otherwise
        """
        return self._user_repository.get_by_id(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[MobileBankingUser]:
        """
        Get a user by their username.
        
        Args:
            username: The username of the user
            
        Returns:
            MobileBankingUser if found, None otherwise
        """
        return self._user_repository.get_by_username(username)
    
    def get_user_by_mobile_number(self, mobile_number: str) -> Optional[MobileBankingUser]:
        """
        Get a user by their mobile number.
        
        Args:
            mobile_number: The mobile number of the user
            
        Returns:
            MobileBankingUser if found, None otherwise
        """
        return self._user_repository.get_by_mobile_number(mobile_number)
