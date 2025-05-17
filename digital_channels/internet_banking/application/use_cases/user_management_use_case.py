"""
User management use cases for the Internet Banking domain.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from ...domain.entities.user import InternetBankingUser, UserStatus
from ...domain.services.authentication_service import AuthenticationService
from ...domain.validators.input_validator import InputValidator
from ..interfaces.user_repository_interface import UserRepositoryInterface
from ..interfaces.notification_service_interface import NotificationServiceInterface, NotificationType
from ..interfaces.audit_log_service_interface import AuditLogServiceInterface, AuditEventType


@dataclass
class UserCreationResult:
    """Result of a user creation attempt."""
    success: bool
    message: str
    user: Optional[InternetBankingUser] = None


@dataclass
class UserUpdateResult:
    """Result of a user update attempt."""
    success: bool
    message: str
    user: Optional[InternetBankingUser] = None


class UserManagementUseCase:
    """Use cases related to user management."""
    
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        notification_service: NotificationServiceInterface,
        audit_log_service: AuditLogServiceInterface,
        auth_service: AuthenticationService,
        input_validator: InputValidator
    ):
        """
        Initialize the user management use case.
        
        Args:
            user_repository: Repository for user operations
            notification_service: Service for sending notifications
            audit_log_service: Service for logging audit events
            auth_service: Domain service for authentication
            input_validator: Validator for input data
        """
        self._user_repository = user_repository
        self._notification_service = notification_service
        self._audit_log_service = audit_log_service
        self._auth_service = auth_service
        self._input_validator = input_validator
    
    def create_user(
        self,
        customer_id: UUID,
        email: str,
        phone_number: str,
        username: str,
        password: str,
        admin_user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> UserCreationResult:
        """
        Create a new Internet Banking user.
        
        Args:
            customer_id: ID of the associated customer
            email: Email address
            phone_number: Phone number
            username: Username for login
            password: Password (will be hashed)
            admin_user_id: ID of the admin user performing the action (if applicable)
            ip_address: IP address of the client
            
        Returns:
            UserCreationResult with result information
        """
        # Validate inputs
        is_valid, error = self._input_validator.validate_email(email)
        if not is_valid:
            return UserCreationResult(
                success=False,
                message=f"Invalid email: {error}"
            )
        
        is_valid, error = self._input_validator.validate_phone_number(phone_number)
        if not is_valid:
            return UserCreationResult(
                success=False,
                message=f"Invalid phone number: {error}"
            )
        
        is_valid, error = self._input_validator.validate_username(username)
        if not is_valid:
            return UserCreationResult(
                success=False,
                message=f"Invalid username: {error}"
            )
        
        # Check if username is already taken
        existing_user = self._user_repository.get_by_username(username)
        if existing_user is not None:
            return UserCreationResult(
                success=False,
                message="Username is already taken"
            )
        
        # Hash the password
        password_hash, salt = self._auth_service.generate_password_hash(password)
        
        # Create the user
        user = InternetBankingUser.create(
            customer_id=customer_id,
            email=email,
            phone_number=phone_number,
            username=username,
            password_hash=password_hash,
            salt=salt
        )
        
        # Save the user
        saved_user = self._user_repository.save(user)
        
        # Log the user creation
        self._audit_log_service.log_event(
            event_type=AuditEventType.USER_CREATED,
            user_id=admin_user_id,
            details={
                "created_user_id": str(saved_user.user_id),
                "username": username,
                "customer_id": str(customer_id)
            },
            ip_address=ip_address,
            status="success"
        )
        
        # Send welcome notification
        self._notification_service.send_email(
            to_email=email,
            subject="Welcome to Internet Banking",
            message=f"Your Internet Banking account has been created. "
                    f"Your username is {username}. Please activate your account.",
            notification_type=NotificationType.ACCOUNT_CREATED
        )
        
        return UserCreationResult(
            success=True,
            message="User created successfully. Activation required.",
            user=saved_user
        )
    
    def activate_user(
        self,
        user_id: UUID,
        activation_code: str,
        admin_user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> UserUpdateResult:
        """
        Activate a user account.
        
        Args:
            user_id: ID of the user to activate
            activation_code: Activation code for verification
            admin_user_id: ID of the admin user performing the action (if applicable)
            ip_address: IP address of the client
            
        Returns:
            UserUpdateResult with result information
        """
        # Find the user
        user = self._user_repository.get_by_id(user_id)
        
        # User not found
        if user is None:
            return UserUpdateResult(
                success=False,
                message="User not found"
            )
        
        # In a real implementation, verify the activation code
        # For this example, we'll just activate the user
        
        try:
            # Activate the user
            user.activate()
            saved_user = self._user_repository.save(user)
            
            # Log the activation
            self._audit_log_service.log_event(
                event_type=AuditEventType.USER_ACTIVATED,
                user_id=admin_user_id or user_id,
                details={"activated_user_id": str(user_id)},
                ip_address=ip_address,
                status="success"
            )
            
            # Send activation notification
            self._notification_service.send_email(
                to_email=user.email,
                subject="Your Internet Banking account has been activated",
                message="Your Internet Banking account has been activated. You can now log in.",
                notification_type=NotificationType.ACCOUNT_UPDATE
            )
            
            return UserUpdateResult(
                success=True,
                message="User activated successfully",
                user=saved_user
            )
        except ValueError as e:
            return UserUpdateResult(
                success=False,
                message=str(e)
            )
    
    def update_user_profile(
        self,
        user_id: UUID,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        session_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> UserUpdateResult:
        """
        Update a user's profile information.
        
        Args:
            user_id: ID of the user to update
            email: New email address (if updating)
            phone_number: New phone number (if updating)
            session_id: ID of the current session (if applicable)
            ip_address: IP address of the client
            
        Returns:
            UserUpdateResult with result information
        """
        # Find the user
        user = self._user_repository.get_by_id(user_id)
        
        # User not found
        if user is None:
            return UserUpdateResult(
                success=False,
                message="User not found"
            )
        
        # Update email if provided
        if email is not None and email != user.email:
            is_valid, error = self._input_validator.validate_email(email)
            if not is_valid:
                return UserUpdateResult(
                    success=False,
                    message=f"Invalid email: {error}"
                )
            
            user.update_email(email)
        
        # Update phone number if provided
        if phone_number is not None and phone_number != user.phone_number:
            is_valid, error = self._input_validator.validate_phone_number(phone_number)
            if not is_valid:
                return UserUpdateResult(
                    success=False,
                    message=f"Invalid phone number: {error}"
                )
            
            user.update_phone(phone_number)
        
        # Save the user
        saved_user = self._user_repository.save(user)
        
        # Log the profile update
        self._audit_log_service.log_event(
            event_type=AuditEventType.PROFILE_UPDATE,
            user_id=user_id,
            session_id=session_id,
            details={
                "updated_fields": {
                    "email": email is not None,
                    "phone_number": phone_number is not None
                }
            },
            ip_address=ip_address,
            status="success"
        )
        
        # Send profile update notification
        self._notification_service.send_email(
            to_email=user.email,
            subject="Your profile has been updated",
            message="Your Internet Banking profile has been updated.",
            notification_type=NotificationType.ACCOUNT_UPDATE
        )
        
        return UserUpdateResult(
            success=True,
            message="Profile updated successfully",
            user=saved_user
        )
    
    def lock_user(
        self,
        user_id: UUID,
        admin_user_id: Optional[UUID] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> UserUpdateResult:
        """
        Lock a user account.
        
        Args:
            user_id: ID of the user to lock
            admin_user_id: ID of the admin user performing the action (if applicable)
            reason: Reason for locking the account
            ip_address: IP address of the client
            
        Returns:
            UserUpdateResult with result information
        """
        # Find the user
        user = self._user_repository.get_by_id(user_id)
        
        # User not found
        if user is None:
            return UserUpdateResult(
                success=False,
                message="User not found"
            )
        
        try:
            # Lock the user
            user.lock()
            saved_user = self._user_repository.save(user)
            
            # Log the lock
            self._audit_log_service.log_event(
                event_type=AuditEventType.USER_LOCKED,
                user_id=admin_user_id or user_id,
                details={
                    "locked_user_id": str(user_id),
                    "reason": reason or "Manual lock"
                },
                ip_address=ip_address,
                status="success"
            )
            
            # Send lock notification
            self._notification_service.send_email(
                to_email=user.email,
                subject="Your Internet Banking account has been locked",
                message="Your Internet Banking account has been locked. Please contact customer support.",
                notification_type=NotificationType.SECURITY_ALERT
            )
            
            return UserUpdateResult(
                success=True,
                message="User locked successfully",
                user=saved_user
            )
        except ValueError as e:
            return UserUpdateResult(
                success=False,
                message=str(e)
            )
    
    def get_users_by_status(self, status: UserStatus) -> List[InternetBankingUser]:
        """
        Get a list of users by status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of users with the specified status
        """
        # In a real implementation, we would have a repository method for this
        # For this example, we'll use the list_active_users method for active users
        if status == UserStatus.ACTIVE:
            return self._user_repository.list_active_users()
        
        # For other statuses, we would need to implement specific methods
        return []
