"""
Security service implementation.
"""
from typing import Dict, List, Optional, Any
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from dashboard.domain.entities.admin_user import AdminUser, AdminRole
from dashboard.application.interfaces.services import SecurityService
from dashboard.application.interfaces.repositories import AdminUserRepository
from dashboard.domain.entities.audit_log import AuditLog, AuditLogAction, AuditLogSeverity
from dashboard.application.interfaces.repositories import AuditLogRepository


class SecurityServiceImpl(SecurityService):
    """Implementation of the SecurityService interface."""
    
    def __init__(
        self, 
        admin_user_repository: AdminUserRepository,
        audit_log_repository: AuditLogRepository
    ):
        self.admin_user_repository = admin_user_repository
        self.audit_log_repository = audit_log_repository
        self.secret_key = settings.SECRET_KEY
        self.token_expiry = timedelta(hours=1)  # Default token expiry time
    
    def authenticate_user(self, username: str, password: str, ip_address: str = None) -> Optional[str]:
        """Authenticate a user and return a token."""
        user = self.admin_user_repository.authenticate_user(username, password)
        
        if not user:
            # Log failed login attempt
            if ip_address:
                self.audit_log_repository.create_log(
                    AuditLog(
                        user_id=None,
                        action=AuditLogAction.LOGIN,
                        resource_type="admin_user",
                        resource_id=username,  # We don't have a user ID for failed logins
                        severity=AuditLogSeverity.WARNING,
                        details={"username": username},
                        ip_address=ip_address,
                        success=False,
                        error_message="Invalid username or password"
                    )
                )
            return None
        
        # Generate JWT token
        payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role.value,
            'exp': datetime.utcnow() + self.token_expiry
        }
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        # Log successful login
        if ip_address:
            self.audit_log_repository.create_log(
                AuditLog(
                    user_id=user.id,
                    action=AuditLogAction.LOGIN,
                    resource_type="admin_user",
                    resource_id=user.id,
                    severity=AuditLogSeverity.INFO,
                    details={"username": user.username},
                    ip_address=ip_address,
                    success=True
                )
            )
        
        return token
    
    def validate_token(self, token: str) -> Optional[AdminUser]:
        """Validate a token and return the associated user."""
        try:
            # Decode and validate the token
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Get user from repository
            user_id = payload.get('user_id')
            if not user_id:
                return None
            
            return self.admin_user_repository.get_user_by_id(user_id)
        except jwt.ExpiredSignatureError:
            # Token has expired
            return None
        except jwt.InvalidTokenError:
            # Token is invalid
            return None
    
    def change_password(self, user_id: str, old_password: str, new_password: str, ip_address: str = None) -> bool:
        """Change a user's password."""
        # Get the user
        user = self.admin_user_repository.get_user_by_id(user_id)
        if not user:
            return False
        
        # Authenticate with old password
        authenticated_user = self.admin_user_repository.authenticate_user(user.username, old_password)
        if not authenticated_user:
            # Log failed password change
            if ip_address:
                self.audit_log_repository.create_log(
                    AuditLog(
                        user_id=user_id,
                        action=AuditLogAction.UPDATE,
                        resource_type="admin_user_password",
                        resource_id=user_id,
                        severity=AuditLogSeverity.WARNING,
                        details={"username": user.username},
                        ip_address=ip_address,
                        success=False,
                        error_message="Invalid old password"
                    )
                )
            return False
        
        # Change password (using Django's built-in methods)
        # Note: This is simplified - in a real implementation we would need to access
        # the Django user model to set the password correctly
        user_model = authenticated_user._user_model
        user_model.set_password(new_password)
        user_model.save()
        
        # Log successful password change
        if ip_address:
            self.audit_log_repository.create_log(
                AuditLog(
                    user_id=user_id,
                    action=AuditLogAction.UPDATE,
                    resource_type="admin_user_password",
                    resource_id=user_id,
                    severity=AuditLogSeverity.INFO,
                    details={"username": user.username},
                    ip_address=ip_address,
                    success=True
                )
            )
        
        return True
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if a user has a specific permission."""
        user = self.admin_user_repository.get_user_by_id(user_id)
        if not user:
            return False
        
        # Map permissions to roles
        role_permissions = {
            AdminRole.SUPER_ADMIN: ['*'],  # Super admin has all permissions
            AdminRole.SYSTEM_ADMIN: ['manage_modules', 'manage_apis', 'manage_configs', 'view_logs'],
            AdminRole.MODULE_ADMIN: ['manage_modules', 'view_logs'],
            AdminRole.API_ADMIN: ['manage_apis', 'view_logs'],
            AdminRole.AUDIT_ADMIN: ['view_logs'],
            AdminRole.READONLY_ADMIN: ['view_modules', 'view_apis', 'view_configs', 'view_logs']
        }
        
        user_permissions = role_permissions.get(user.role, [])
        
        # Check if user has the requested permission
        return permission in user_permissions or '*' in user_permissions
