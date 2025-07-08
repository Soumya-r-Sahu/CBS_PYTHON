"""
Admin User entity for the admin dashboard.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class AdminRole(Enum):
    """Roles available for admin users."""
    SUPER_ADMIN = "super_admin"
    SYSTEM_ADMIN = "system_admin"
    MODULE_ADMIN = "module_admin"
    API_ADMIN = "api_admin"
    AUDIT_ADMIN = "audit_admin"
    READONLY_ADMIN = "readonly_admin"


class AdminPermission(Enum):
    """Permissions available for admin users."""
    MANAGE_MODULES = "manage_modules"
    MANAGE_APIS = "manage_apis"
    MANAGE_FEATURES = "manage_features"
    MANAGE_USERS = "manage_users"
    VIEW_LOGS = "view_logs"
    VIEW_HEALTH = "view_health"
    MANAGE_CONFIGURATION = "manage_configuration"


@dataclass
class AdminUser:
    """Admin User entity representing an administrator of the CBS system."""
    id: str
    username: str
    email: str
    role: AdminRole
    permissions: List[AdminPermission] = field(default_factory=list)
    is_active: bool = True
    full_name: Optional[str] = None
    last_login: Optional[str] = None
    mfa_enabled: bool = False
