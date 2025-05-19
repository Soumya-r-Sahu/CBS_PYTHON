"""
Audit Log entity for the admin dashboard.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class AuditLogAction(Enum):
    """Types of audit log actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ENABLE = "enable"
    DISABLE = "disable"
    CONFIGURE = "configure"
    RESTART = "restart"


class AuditLogSeverity(Enum):
    """Severity levels for audit logs."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditLog:
    """Audit Log entity representing an administrative action in the system."""
    id: str
    timestamp: str
    user_id: str
    action: AuditLogAction
    resource_type: str  # Module, ApiEndpoint, FeatureFlag, etc.
    resource_id: str
    severity: AuditLogSeverity = AuditLogSeverity.INFO
    details: Optional[Dict] = None
    ip_address: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
