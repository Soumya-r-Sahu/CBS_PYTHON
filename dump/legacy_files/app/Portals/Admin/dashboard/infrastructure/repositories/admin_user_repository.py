"""
Admin user repository implementation.
"""
from typing import Dict, List, Optional, Any
from django.contrib.auth import authenticate
from dashboard.domain.entities.admin_user import AdminUser as AdminUserEntity, AdminRole as AdminRoleEntity
from dashboard.application.interfaces.repositories import AdminUserRepository
from dashboard.models import AdminUser as AdminUserModel, AdminRole


class DjangoAdminUserRepository(AdminUserRepository):
    """Django implementation of the AdminUserRepository interface."""

    def get_all_users(self) -> List[AdminUserEntity]:
        """Get all admin users."""
        users = AdminUserModel.objects.all()
        return [self._to_entity(user) for user in users]
    
    def get_user_by_id(self, user_id: str) -> Optional[AdminUserEntity]:
        """Get an admin user by their ID."""
        try:
            user = AdminUserModel.objects.get(id=user_id)
            return self._to_entity(user)
        except AdminUserModel.DoesNotExist:
            return None
    
    def get_user_by_username(self, username: str) -> Optional[AdminUserEntity]:
        """Get an admin user by their username."""
        try:
            user = AdminUserModel.objects.get(username=username)
            return self._to_entity(user)
        except AdminUserModel.DoesNotExist:
            return None
    
    def create_user(self, user: AdminUserEntity, password: str) -> AdminUserEntity:
        """Create a new admin user."""
        model = AdminUserModel.objects.create_user(
            username=user.username,
            email=user.email,
            password=password,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            mfa_enabled=user.mfa_enabled
        )
        return self._to_entity(model)
    
    def update_user(self, user: AdminUserEntity) -> AdminUserEntity:
        """Update an existing admin user."""
        try:
            model = AdminUserModel.objects.get(id=user.id)
            model.username = user.username
            model.email = user.email
            model.first_name = user.first_name
            model.last_name = user.last_name
            model.role = user.role.value
            model.mfa_enabled = user.mfa_enabled
            model.save()
            return self._to_entity(model)
        except AdminUserModel.DoesNotExist:
            return None
    
    def delete_user(self, user_id: str) -> bool:
        """Delete an admin user by their ID."""
        try:
            user = AdminUserModel.objects.get(id=user_id)
            user.delete()
            return True
        except AdminUserModel.DoesNotExist:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[AdminUserEntity]:
        """Authenticate an admin user with their username and password."""
        user = authenticate(username=username, password=password)
        if user is not None and isinstance(user, AdminUserModel):
            return self._to_entity(user)
        return None
    
    def _to_entity(self, model: AdminUserModel) -> AdminUserEntity:
        """Convert a Django model to a domain entity."""
        return AdminUserEntity(
            id=str(model.id),
            username=model.username,
            email=model.email,
            first_name=model.first_name,
            last_name=model.last_name,
            role=AdminRoleEntity(model.role),
            mfa_enabled=model.mfa_enabled,
            is_active=model.is_active,
            date_joined=model.date_joined.isoformat() if model.date_joined else None,
            last_login=model.last_login.isoformat() if model.last_login else None
        )
