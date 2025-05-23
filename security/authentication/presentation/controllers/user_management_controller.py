"""
User management controller for handling user-related operations.
This is part of the presentation layer that receives requests related to 
user creation, updates, password resets, etc.
"""

from typing import Dict, Any, Tuple, Optional, List
import uuid

from security.authentication.domain.entities.user import User
from security.authentication.domain.value_objects.user_id import UserId
from security.authentication.domain.value_objects.credential import Credential
from security.authentication.domain.value_objects.user_status import UserStatus
from security.authentication.domain.repositories.user_repository import UserRepository
from security.authentication.domain.services.password_policy_service import PasswordPolicyService
from security.authentication.domain.services.audit_service import AuditService
from security.common.security_utils import SecurityException, AuthenticationException, PasswordUtils


class UserManagementController:
    """Controller for handling user management operations."""
    
    def __init__(
        self,
        user_repository: UserRepository,
        password_policy_service: PasswordPolicyService,
        audit_service: AuditService
    ):
        """Initialize the user management controller.
        
        Args:
            user_repository: Repository for user data access
            password_policy_service: Service for password policy enforcement
            audit_service: Service for audit logging
        """
        self.user_repository = user_repository
        self.password_policy_service = password_policy_service
        self.audit_service = audit_service
    
    def create_user(
        self,
        username: str,
        password: str,
        email: str,
        full_name: str,
        admin_username: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Create a new user.
        
        Args:
            username: Username for the new user
            password: Initial password
            email: Email address
            full_name: Full name of the user
            admin_username: Username of the admin performing the action
            ip_address: IP address of the client (for audit logging)
            
        Returns:
            Tuple of (success, response_data)
        """
        try:
            # Check if username already exists
            existing_user = self.user_repository.find_by_username(username)
            if existing_user:
                return False, {
                    "success": False,
                    "message": f"Username '{username}' already exists"
                }
            
            # Check if email already exists
            existing_email = self.user_repository.find_by_email(email)
            if existing_email:
                return False, {
                    "success": False,
                    "message": f"Email '{email}' already registered"
                }
            
            # Validate password against policy
            if not self.password_policy_service.validate_password(password):
                return False, {
                    "success": False,
                    "message": "Password does not meet security requirements"
                }
            
            # Create password hash and salt
            password_hash, salt = PasswordUtils.hash_password(password)
            
            # Create new user
            user_id = UserId(str(uuid.uuid4()))
            new_user = User(
                user_id=user_id,
                username=username,
                credential=Credential(password_hash, salt),
                email=email,
                full_name=full_name,
                status=UserStatus.ACTIVE,
                requires_password_change=True  # Force password change on first login
            )
            
            # Save user
            self.user_repository.save(new_user)
            
            # Log user creation
            self.audit_service.log_security_event(
                event_type="USER_CREATION",
                description=f"New user '{username}' created",
                severity="INFO",
                username=admin_username,
                ip_address=ip_address,
                details={"user_id": user_id.value, "email": email}
            )
            
            # Return success response
            return True, {
                "success": True,
                "message": f"User '{username}' created successfully",
                "user_id": user_id.value
            }
            
        except Exception as e:
            # Log error
            self.audit_service.log_security_event(
                event_type="USER_CREATION_ERROR",
                description=f"Failed to create user '{username}'",
                severity="ERROR",
                username=admin_username,
                ip_address=ip_address,
                details={"error": str(e)}
            )
            
            # Return error response
            return False, {
                "success": False,
                "message": f"Failed to create user: {str(e)}"
            }
    
    def update_user_status(
        self,
        user_id: str,
        new_status: str,
        admin_username: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a user's status (active, locked, disabled).
        
        Args:
            user_id: ID of the user to update
            new_status: New status to set
            admin_username: Username of the admin performing the action
            ip_address: IP address of the client (for audit logging)
            
        Returns:
            Response data as dictionary
        """
        try:
            # Validate status
            try:
                status = UserStatus(new_status)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid status: {new_status}"
                }
            
            # Retrieve user
            user = self.user_repository.find_by_id(UserId(user_id))
            if not user:
                return {
                    "success": False,
                    "message": f"User with ID '{user_id}' not found"
                }
            
            # Update status
            old_status = user.status.value
            user.status = status
            
            # Save updated user
            self.user_repository.save(user)
            
            # Log status change
            self.audit_service.log_security_event(
                event_type="USER_STATUS_CHANGE",
                description=f"User '{user.username}' status changed from {old_status} to {new_status}",
                severity="INFO",
                username=admin_username,
                ip_address=ip_address,
                details={"user_id": user_id, "old_status": old_status, "new_status": new_status}
            )
            
            # Return success response
            return {
                "success": True,
                "message": f"User status updated to {new_status}"
            }
            
        except Exception as e:
            # Log error
            self.audit_service.log_security_event(
                event_type="USER_STATUS_CHANGE_ERROR",
                description=f"Failed to update user status",
                severity="ERROR",
                username=admin_username,
                ip_address=ip_address,
                details={"user_id": user_id, "error": str(e)}
            )
            
            # Return error response
            return {
                "success": False,
                "message": f"Failed to update user status: {str(e)}"
            }
    
    def reset_password(
        self,
        user_id: str,
        new_password: str,
        admin_username: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reset a user's password.
        
        Args:
            user_id: ID of the user whose password to reset
            new_password: New password to set
            admin_username: Username of the admin performing the action
            ip_address: IP address of the client (for audit logging)
            
        Returns:
            Response data as dictionary
        """
        try:
            # Validate password against policy
            if not self.password_policy_service.validate_password(new_password):
                return {
                    "success": False,
                    "message": "Password does not meet security requirements"
                }
            
            # Retrieve user
            user = self.user_repository.find_by_id(UserId(user_id))
            if not user:
                return {
                    "success": False,
                    "message": f"User with ID '{user_id}' not found"
                }
            
            # Create password hash and salt
            password_hash, salt = PasswordUtils.hash_password(new_password)
            
            # Update user credentials
            user.credential = Credential(password_hash, salt)
            user.requires_password_change = True  # Force user to change password on next login
            
            # Save updated user
            self.user_repository.save(user)
            
            # Log password reset
            self.audit_service.log_security_event(
                event_type="PASSWORD_RESET",
                description=f"Password reset for user '{user.username}'",
                severity="INFO",
                username=admin_username,
                ip_address=ip_address,
                details={"user_id": user_id}
            )
            
            # Return success response
            return {
                "success": True,
                "message": f"Password for user '{user.username}' has been reset"
            }
            
        except Exception as e:
            # Log error
            self.audit_service.log_security_event(
                event_type="PASSWORD_RESET_ERROR",
                description=f"Failed to reset password",
                severity="ERROR",
                username=admin_username,
                ip_address=ip_address,
                details={"user_id": user_id, "error": str(e)}
            )
            
            # Return error response
            return {
                "success": False,
                "message": f"Failed to reset password: {str(e)}"
            }
    
    def get_user_list(self) -> List[Dict[str, Any]]:
        """Get a list of all users.
        
        Returns:
            List of user data dictionaries
        """
        try:
            # Retrieve all users
            users = self.user_repository.find_all()
            
            # Map to response format
            user_list = []
            for user in users:
                user_list.append({
                    "id": user.id.value,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "status": user.status.value,
                    "created_at": user.creation_date,
                    "last_login": user.last_login_date
                })
            
            return user_list
            
        except Exception as e:
            # Return empty list on error
            return []
