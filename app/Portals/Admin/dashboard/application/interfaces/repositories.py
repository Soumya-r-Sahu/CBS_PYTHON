"""
Repository interfaces for the admin dashboard.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from ...domain.entities.module import Module, ModuleStatus
from ...domain.entities.api_endpoint import ApiEndpoint
from ...domain.entities.admin_user import AdminUser
from ...domain.entities.system_config import SystemConfig
from ...domain.entities.audit_log import AuditLog
from ...domain.entities.system_health import SystemHealth


class ModuleRepository(ABC):
    """Repository interface for Module entities."""
    
    @abstractmethod
    def get_all_modules(self) -> List[Module]:
        """Get all modules."""
        pass
    
    @abstractmethod
    def get_module_by_id(self, module_id: str) -> Optional[Module]:
        """Get a module by its ID."""
        pass
    
    @abstractmethod
    def create_module(self, module: Module) -> Module:
        """Create a new module."""
        pass
    
    @abstractmethod
    def update_module(self, module: Module) -> Module:
        """Update an existing module."""
        pass
    
    @abstractmethod
    def delete_module(self, module_id: str) -> bool:
        """Delete a module by its ID."""
        pass
    
    @abstractmethod
    def update_module_status(self, module_id: str, status: ModuleStatus) -> Module:
        """Update a module's status."""
        pass
    
    @abstractmethod
    def get_modules_by_status(self, status: ModuleStatus) -> List[Module]:
        """Get all modules with a specific status."""
        pass


class ApiEndpointRepository(ABC):
    """Repository interface for ApiEndpoint entities."""
    
    @abstractmethod
    def get_all_endpoints(self) -> List[ApiEndpoint]:
        """Get all API endpoints."""
        pass
    
    @abstractmethod
    def get_endpoint_by_id(self, endpoint_id: str) -> Optional[ApiEndpoint]:
        """Get an API endpoint by its ID."""
        pass
    
    @abstractmethod
    def get_endpoints_by_module(self, module_id: str) -> List[ApiEndpoint]:
        """Get all API endpoints for a specific module."""
        pass
    
    @abstractmethod
    def create_endpoint(self, endpoint: ApiEndpoint) -> ApiEndpoint:
        """Create a new API endpoint."""
        pass
    
    @abstractmethod
    def update_endpoint(self, endpoint: ApiEndpoint) -> ApiEndpoint:
        """Update an existing API endpoint."""
        pass
    
    @abstractmethod
    def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete an API endpoint by its ID."""
        pass
    
    @abstractmethod
    def toggle_endpoint(self, endpoint_id: str, enabled: bool) -> ApiEndpoint:
        """Enable or disable an API endpoint."""
        pass


class AdminUserRepository(ABC):
    """Repository interface for AdminUser entities."""
    
    @abstractmethod
    def get_all_users(self) -> List[AdminUser]:
        """Get all admin users."""
        pass
    
    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[AdminUser]:
        """Get an admin user by their ID."""
        pass
    
    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[AdminUser]:
        """Get an admin user by their username."""
        pass
    
    @abstractmethod
    def create_user(self, user: AdminUser, password: str) -> AdminUser:
        """Create a new admin user."""
        pass
    
    @abstractmethod
    def update_user(self, user: AdminUser) -> AdminUser:
        """Update an existing admin user."""
        pass
    
    @abstractmethod
    def delete_user(self, user_id: str) -> bool:
        """Delete an admin user by their ID."""
        pass
    
    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> Optional[AdminUser]:
        """Authenticate an admin user with their username and password."""
        pass


class SystemConfigRepository(ABC):
    """Repository interface for SystemConfig entities."""
    
    @abstractmethod
    def get_all_configs(self) -> List[SystemConfig]:
        """Get all system configurations."""
        pass
    
    @abstractmethod
    def get_config_by_id(self, config_id: str) -> Optional[SystemConfig]:
        """Get a system configuration by its ID."""
        pass
    
    @abstractmethod
    def get_configs_by_module(self, module_id: str) -> List[SystemConfig]:
        """Get all system configurations for a specific module."""
        pass
    
    @abstractmethod
    def get_config_by_key(self, key: str) -> Optional[SystemConfig]:
        """Get a system configuration by its key."""
        pass
    
    @abstractmethod
    def create_config(self, config: SystemConfig) -> SystemConfig:
        """Create a new system configuration."""
        pass
    
    @abstractmethod
    def update_config(self, config: SystemConfig) -> SystemConfig:
        """Update an existing system configuration."""
        pass
    
    @abstractmethod
    def delete_config(self, config_id: str) -> bool:
        """Delete a system configuration by its ID."""
        pass


class AuditLogRepository(ABC):
    """Repository interface for AuditLog entities."""
    
    @abstractmethod
    def get_all_logs(self, limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """Get all audit logs with pagination."""
        pass
    
    @abstractmethod
    def get_log_by_id(self, log_id: str) -> Optional[AuditLog]:
        """Get an audit log by its ID."""
        pass
    
    @abstractmethod
    def get_logs_by_user(self, user_id: str, limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """Get all audit logs for a specific user."""
        pass
    
    @abstractmethod
    def get_logs_by_resource(self, resource_type: str, resource_id: str, limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """Get all audit logs for a specific resource."""
        pass
    
    @abstractmethod
    def create_log(self, log: AuditLog) -> AuditLog:
        """Create a new audit log."""
        pass
    
    @abstractmethod
    def search_logs(self, criteria: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """Search audit logs based on criteria."""
        pass


class SystemHealthRepository(ABC):
    """Repository interface for SystemHealth entities."""
    
    @abstractmethod
    def get_all_health_metrics(self) -> List[SystemHealth]:
        """Get all system health metrics."""
        pass
    
    @abstractmethod
    def get_health_by_component(self, component: str) -> Optional[SystemHealth]:
        """Get health metrics for a specific component."""
        pass
    
    @abstractmethod
    def create_health_metric(self, health: SystemHealth) -> SystemHealth:
        """Create a new health metric record."""
        pass
    
    @abstractmethod
    def update_health_metric(self, health: SystemHealth) -> SystemHealth:
        """Update an existing health metric record."""
        pass
    
    @abstractmethod
    def get_historical_health(self, component: str, start_time: str, end_time: str) -> List[SystemHealth]:
        """Get historical health metrics for a component."""
        pass
