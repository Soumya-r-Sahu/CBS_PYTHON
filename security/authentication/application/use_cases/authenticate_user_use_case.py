"""
Authenticate User Use Case

This module implements the use case for authenticating users.
It coordinates the authentication process and applies business rules.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from ...domain.repositories.user_repository import UserRepository
from ...domain.entities.user import User
from ...domain.value_objects.user_status import UserStatus


@dataclass
class AuthenticateUserInputDto:
    """Data Transfer Object for user authentication input"""
    username: str
    password: str
    ip_address: Optional[str] = None


@dataclass
class AuthenticateUserOutputDto:
    """Data Transfer Object for user authentication output"""
    success: bool
    user_id: Optional[str] = None
    token: Optional[str] = None
    full_name: Optional[str] = None
    roles: Optional[list] = None
    requires_mfa: bool = False
    error_message: Optional[str] = None


class AuthenticateUserUseCase:
    """
    Use case for authenticating users
    
    This class implements the application business rules for user authentication,
    coordinating between domain entities and repositories.
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        token_service,  # Will be defined in interfaces
        audit_service,  # Will be defined in interfaces
    ):
        """
        Initialize the use case with required repositories and services
        
        Args:
            user_repository: Repository for user data access
            token_service: Service for generating authentication tokens
            audit_service: Service for logging authentication events
        """
        self._user_repository = user_repository
        self._token_service = token_service
        self._audit_service = audit_service
    
    def execute(
        self, 
        input_dto: AuthenticateUserInputDto
    ) -> AuthenticateUserOutputDto:
        """
        Execute the authentication process
        
        Args:
            input_dto: Authentication input data
            
        Returns:
            Authentication result
        """
        # Find the user
        user = self._user_repository.get_by_username(input_dto.username)
        
        # If user not found, check by email
        if not user:
            user = self._user_repository.get_by_email(input_dto.username)
        
        # If still not found, authentication fails
        if not user:
            self._log_failed_attempt(input_dto, "User not found")
            return AuthenticateUserOutputDto(
                success=False,
                error_message="Invalid username or password"
            )
        
        # Check if account is active
        if not user.status.is_active():
            error_message = f"Account is {user.status.status.name.lower()}"
            self._log_failed_attempt(input_dto, error_message, user)
            return AuthenticateUserOutputDto(
                success=False,
                error_message=error_message
            )
        
        # Check if account is locked
        if user.is_locked():
            self._log_failed_attempt(input_dto, "Account is locked", user)
            return AuthenticateUserOutputDto(
                success=False,
                error_message="Account is locked due to too many failed attempts"
            )
        
        # Authenticate user
        if not user.authenticate(input_dto.password):
            # Update user with failed attempt counter
            self._user_repository.update(user)
            
            self._log_failed_attempt(input_dto, "Invalid password", user)
            return AuthenticateUserOutputDto(
                success=False,
                error_message="Invalid username or password"
            )
        
        # Authentication successful
        # Update last login time
        user.last_login = datetime.now()
        user.login_attempts = 0  # Reset failed attempts
        self._user_repository.update(user)
        
        # Generate token
        token = self._token_service.generate_token(str(user.id), user.roles)
        
        # Log successful authentication
        self._audit_service.log_authentication(
            user_id=str(user.id),
            username=user.username,
            ip_address=input_dto.ip_address,
            success=True
        )
        
        # Return successful result
        return AuthenticateUserOutputDto(
            success=True,
            user_id=user.user_id.value,
            token=token,
            full_name=f"{user.first_name} {user.last_name}",
            roles=user.roles,
            requires_mfa=user.mfa_enabled
        )
    
    def _log_failed_attempt(
        self, 
        input_dto: AuthenticateUserInputDto, 
        reason: str,
        user: Optional[User] = None
    ) -> None:
        """
        Log a failed authentication attempt
        
        Args:
            input_dto: Authentication input data
            reason: Reason for failure
            user: User entity if available
        """
        self._audit_service.log_authentication(
            user_id=str(user.id) if user else None,
            username=input_dto.username,
            ip_address=input_dto.ip_address,
            success=False,
            failure_reason=reason
        )
