"""
API management service implementation.
"""
from typing import Dict, List, Optional, Any
from dashboard.domain.entities.api_endpoint import ApiEndpoint, HttpMethod
from dashboard.application.interfaces.services import ApiManagementService
from dashboard.application.interfaces.repositories import ApiEndpointRepository, ModuleRepository
from dashboard.domain.entities.audit_log import AuditLog, AuditLogAction, AuditLogSeverity
from dashboard.application.interfaces.repositories import AuditLogRepository


class ApiManagementServiceImpl(ApiManagementService):
    """Implementation of the ApiManagementService interface."""
    
    def __init__(
        self, 
        api_endpoint_repository: ApiEndpointRepository,
        module_repository: ModuleRepository,
        audit_log_repository: AuditLogRepository
    ):
        self.api_endpoint_repository = api_endpoint_repository
        self.module_repository = module_repository
        self.audit_log_repository = audit_log_repository
    
    def toggle_endpoint(self, endpoint_id: str, enabled: bool, user_id: str = None) -> ApiEndpoint:
        """Enable or disable an API endpoint."""
        endpoint = self.api_endpoint_repository.get_endpoint_by_id(endpoint_id)
        if not endpoint:
            raise ValueError(f"API endpoint with ID {endpoint_id} not found")
        
        # Update endpoint status
        updated_endpoint = self.api_endpoint_repository.toggle_endpoint(endpoint_id, enabled)
        
        # Log the action
        if user_id:
            action = AuditLogAction.ENABLE if enabled else AuditLogAction.DISABLE
            self.audit_log_repository.create_log(
                AuditLog(
                    user_id=user_id,
                    action=action,
                    resource_type="api_endpoint",
                    resource_id=endpoint_id,
                    severity=AuditLogSeverity.INFO,
                    details={
                        "path": endpoint.path,
                        "method": endpoint.method.value,
                        "module_id": endpoint.module_id,
                        "enabled": enabled
                    },
                    success=True
                )
            )
        
        return updated_endpoint
    
    def set_rate_limit(self, endpoint_id: str, rate_limit: int, user_id: str = None) -> ApiEndpoint:
        """Set the rate limit for an API endpoint."""
        endpoint = self.api_endpoint_repository.get_endpoint_by_id(endpoint_id)
        if not endpoint:
            raise ValueError(f"API endpoint with ID {endpoint_id} not found")
        
        # Update the endpoint with the new rate limit
        endpoint.rate_limit = rate_limit
        updated_endpoint = self.api_endpoint_repository.update_endpoint(endpoint)
        
        # Log the action
        if user_id:
            self.audit_log_repository.create_log(
                AuditLog(
                    user_id=user_id,
                    action=AuditLogAction.UPDATE,
                    resource_type="api_endpoint",
                    resource_id=endpoint_id,
                    severity=AuditLogSeverity.INFO,
                    details={
                        "path": endpoint.path,
                        "method": endpoint.method.value,
                        "module_id": endpoint.module_id,
                        "old_rate_limit": endpoint.rate_limit,
                        "new_rate_limit": rate_limit
                    },
                    success=True
                )
            )
        
        return updated_endpoint
    
    def discover_endpoints(self, module_id: str = None) -> List[ApiEndpoint]:
        """Discover API endpoints from a module or the entire system."""
        # In a real implementation, this method would dynamically scan modules for endpoints
        # For now, we'll just return existing endpoints from the repository
        
        if module_id:
            return self.api_endpoint_repository.get_endpoints_by_module(module_id)
        else:
            return self.api_endpoint_repository.get_all_endpoints()
