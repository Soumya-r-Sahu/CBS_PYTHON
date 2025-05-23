"""
Authentication controller for handling authentication-related requests.
This is part of the presentation layer that receives requests from the UI
or API and delegates to the appropriate use cases.
"""

from typing import Dict, Any, Tuple, Optional
import json

from security.authentication.application.use_cases.authenticate_user_use_case import AuthenticateUserUseCase
from security.authentication.domain.services.token_service import TokenService
from security.authentication.domain.services.audit_service import AuditService
from security.common.security_utils import SecurityException, AuthenticationException


class AuthenticationController:
    """Controller for handling authentication-related requests."""
    
    def __init__(
        self,
        authenticate_user_use_case: AuthenticateUserUseCase,
        token_service: TokenService,
        audit_service: AuditService
    ):
        """Initialize the authentication controller.
        
        Args:
            authenticate_user_use_case: Use case for authenticating users
            token_service: Service for JWT token operations
            audit_service: Service for audit logging
        """
        self.authenticate_user_use_case = authenticate_user_use_case
        self.token_service = token_service
        self.audit_service = audit_service
    
    def login(
        self, 
        username: str, 
        password: str, 
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Handle user login requests.
        
        Args:
            username: The username to authenticate
            password: The password to verify
            ip_address: The IP address of the client (for audit logging)
            
        Returns:
            Tuple of (success, response_data)
            where response_data contains token on success or error message on failure
        """
        try:
            # Authenticate user
            user = self.authenticate_user_use_case.execute(username, password)
            
            # Generate token
            token = self.token_service.generate_token(
                user_id=user.id.value,
                additional_claims={
                    "username": user.username,
                    "email": user.email,
                    "status": user.status.value
                }
            )
            
            # Log successful authentication
            self.audit_service.log_authentication_event(
                event_type="LOGIN",
                username=username,
                success=True,
                ip_address=ip_address,
                details={"user_id": user.id.value}
            )
            
            # Return success response with token
            return True, {
                "success": True,
                "message": "Authentication successful",
                "token": token,
                "user": {
                    "id": user.id.value,
                    "username": user.username,
                    "email": user.email,
                    "status": user.status.value,
                    "requires_password_change": user.requires_password_change
                }
            }
            
        except (SecurityException, AuthenticationException) as e:
            # Log failed authentication
            self.audit_service.log_authentication_event(
                event_type="LOGIN",
                username=username,
                success=False,
                ip_address=ip_address,
                details={"error": str(e)}
            )
            
            # Return error response
            return False, {
                "success": False,
                "message": str(e)
            }
    
    def logout(self, token: str, username: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Handle user logout requests.
        
        Args:
            token: The authentication token to invalidate
            username: The username logging out (for audit logging)
            ip_address: The IP address of the client (for audit logging)
            
        Returns:
            Response data as dictionary
        """
        try:
            # Validate token first (will throw exception if invalid)
            payload = self.token_service.validate_token(token)
            
            # Blacklist/invalidate the token
            self.token_service.blacklist_token(token)
            
            # Log successful logout
            self.audit_service.log_authentication_event(
                event_type="LOGOUT",
                username=username,
                success=True,
                ip_address=ip_address
            )
            
            # Return success response
            return {
                "success": True,
                "message": "Successfully logged out"
            }
            
        except SecurityException as e:
            # Log attempt to logout with invalid token
            self.audit_service.log_security_event(
                event_type="INVALID_LOGOUT",
                description="Attempted to logout with invalid token",
                severity="WARNING",
                username=username,
                ip_address=ip_address,
                details={"error": str(e)}
            )
            
            # Return error response
            return {
                "success": False,
                "message": str(e)
            }
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify the validity of an authentication token.
        
        Args:
            token: The token to verify
            
        Returns:
            Response data with token validity and payload
        """
        try:
            # Validate token
            payload = self.token_service.validate_token(token)
            
            # Return success response with payload
            return {
                "success": True,
                "valid": True,
                "payload": payload
            }
            
        except SecurityException as e:
            # Return response indicating invalid token
            return {
                "success": True,
                "valid": False,
                "message": str(e)
            }
