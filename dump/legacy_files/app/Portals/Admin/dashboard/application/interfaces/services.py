"""
Service interfaces for the admin dashboard.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from dashboard.domain.entities.module import Module, ModuleStatus
from dashboard.domain.entities.api_endpoint import ApiEndpoint
from dashboard.domain.entities.admin_user import AdminUser
from dashboard.domain.entities.system_config import SystemConfig
from dashboard.domain.entities.system_health import SystemHealth


class ModuleManagementService(ABC):
    """Service interface for managing modules."""
    
    @abstractmethod
    def toggle_module(self, module_id: str, enabled: bool) -> Module:
        """Enable or disable a module."""
        pass
    
    @abstractmethod
    def check_dependencies(self, module_id: str) -> Dict[str, bool]:
        """Check if all dependencies for a module are satisfied."""
        pass
    
    @abstractmethod
    def restart_module(self, module_id: str) -> bool:
        """Restart a module."""
        pass
    
    @abstractmethod
    def install_module(self, module_data: Dict[str, Any]) -> Module:
        """Install a new module."""
        pass
    
    @abstractmethod
    def uninstall_module(self, module_id: str) -> bool:
        """Uninstall a module."""
        pass


class ApiManagementService(ABC):
    """Service interface for managing API endpoints."""
    
    @abstractmethod
    def toggle_endpoint(self, endpoint_id: str, enabled: bool) -> ApiEndpoint:
        """Enable or disable an API endpoint."""
        pass
    
    @abstractmethod
    def set_rate_limit(self, endpoint_id: str, rate_limit: int) -> ApiEndpoint:
        """Set the rate limit for an API endpoint."""
        pass
    
    @abstractmethod
    def discover_endpoints(self, module_id: str = None) -> List[ApiEndpoint]:
        """Discover API endpoints from a module or the entire system."""
        pass


class SecurityService(ABC):
    """Service interface for security operations."""
    
    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate a user and return a token."""
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> Optional[AdminUser]:
        """Validate a token and return the associated user."""
        pass
    
    @abstractmethod
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change a user's password."""
        pass
    
    @abstractmethod
    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if a user has a specific permission."""
        pass


class ConfigurationService(ABC):
    """Service interface for managing system configuration."""
    
    @abstractmethod
    def get_module_configuration(self, module_id: str) -> Dict[str, Any]:
        """Get all configuration for a specific module."""
        pass
    
    @abstractmethod
    def update_configuration(self, config_id: str, value: Any) -> SystemConfig:
        """Update a configuration value."""
        pass
    
    @abstractmethod
    def validate_configuration(self, config: SystemConfig) -> Dict[str, Any]:
        """Validate a configuration value."""
        pass
    
    @abstractmethod
    def apply_configuration(self, config_id: str) -> bool:
        """Apply a configuration change to the running system."""
        pass


class MonitoringService(ABC):
    """Service interface for system monitoring."""
    
    @abstractmethod
    def get_system_health(self) -> Dict[str, SystemHealth]:
        """Get the current health of the entire system."""
        pass
    
    @abstractmethod
    def get_module_health(self, module_id: str) -> SystemHealth:
        """Get the current health of a specific module."""
        pass
    
    @abstractmethod
    def collect_metrics(self) -> Dict[str, Dict[str, float]]:
        """Collect performance metrics from the system."""
        pass
    
    @abstractmethod
    def predict_impact(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Predict the performance impact of configuration changes."""
        pass


class AuditService(ABC):
    """Service interface for audit logging."""
    
    @abstractmethod
    def log_action(self, user_id: str, action: str, resource_type: str, resource_id: str, details: Dict[str, Any] = None) -> bool:
        """Log an administrative action."""
        pass
    
    @abstractmethod
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent administrative activity."""
        pass
    
    @abstractmethod
    def search_logs(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search audit logs based on criteria."""
        pass
