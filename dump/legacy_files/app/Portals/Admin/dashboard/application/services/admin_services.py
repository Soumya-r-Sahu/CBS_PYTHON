"""
Admin Application Services

This module implements the application services for the Admin module.
"""

import logging
from typing import List, Optional, Dict, Any

from dashboard.domain.entities.admin_entities import Module, ApiEndpoint, FeatureFlag, ModuleStatus
from dashboard.application.interfaces.admin_interfaces import (
    ModuleRepository, 
    ApiEndpointRepository,
    FeatureFlagRepository,
    SystemMonitoringService
)

logger = logging.getLogger(__name__)

class ModuleManagementService:
    """Service for managing modules"""
    
    def __init__(self, module_repo: ModuleRepository, endpoint_repo: ApiEndpointRepository, feature_repo: FeatureFlagRepository):
        self.module_repo = module_repo
        self.endpoint_repo = endpoint_repo
        self.feature_repo = feature_repo
    
    def get_all_modules(self) -> List[Module]:
        """Get all modules with their status"""
        return self.module_repo.get_all_modules()
    
    def get_module_details(self, module_id: str) -> Dict[str, Any]:
        """Get detailed information about a module"""
        module = self.module_repo.get_module_by_id(module_id)
        if not module:
            logger.warning(f"Module not found: {module_id}")
            return {}
        
        endpoints = self.endpoint_repo.get_endpoints_by_module(module_id)
        features = self.feature_repo.get_features_by_module(module_id)
        
        return {
            "module": module,
            "endpoints": endpoints,
            "features": features
        }
    
    def toggle_module(self, module_id: str, active: bool) -> Module:
        """Activate or deactivate a module"""
        try:
            module = self.module_repo.toggle_module_status(module_id, active)
            logger.info(f"Module {module_id} toggled to {'active' if active else 'inactive'}")
            return module
        except Exception as e:
            logger.error(f"Failed to toggle module {module_id}: {e}")
            raise
    
    def toggle_feature(self, feature_name: str, module_id: str, enabled: bool) -> FeatureFlag:
        """Toggle a feature flag"""
        try:
            feature = self.feature_repo.toggle_feature(feature_name, module_id, enabled)
            logger.info(f"Feature {feature_name} in module {module_id} toggled to {'enabled' if enabled else 'disabled'}")
            return feature
        except Exception as e:
            logger.error(f"Failed to toggle feature {feature_name} in module {module_id}: {e}")
            raise
    
    def toggle_endpoint(self, endpoint_id: str, enabled: bool) -> ApiEndpoint:
        """Toggle an API endpoint"""
        try:
            endpoint = self.endpoint_repo.toggle_endpoint(endpoint_id, enabled)
            logger.info(f"Endpoint {endpoint_id} toggled to {'enabled' if enabled else 'disabled'}")
            return endpoint
        except Exception as e:
            logger.error(f"Failed to toggle endpoint {endpoint_id}: {e}")
            raise

class SystemMonitoringApplication:
    """Application service for system monitoring"""
    
    def __init__(self, monitoring_service: SystemMonitoringService):
        self.monitoring_service = monitoring_service
    
    def get_system_health_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive system health information for the dashboard"""
        try:
            health = self.monitoring_service.get_system_health()
            resources = self.monitoring_service.get_resource_usage()
            
            dashboard_data = {
                "health": health,
                "resources": resources,
                "status": self._calculate_overall_status(health)
            }
            
            return dashboard_data
        except Exception as e:
            logger.error(f"Failed to get system health dashboard: {e}")
            return {
                "health": {"error": str(e)},
                "resources": {},
                "status": "ERROR"
            }
    
    def _calculate_overall_status(self, health_data: Dict[str, Any]) -> str:
        """Calculate overall system status based on health metrics"""
        if not health_data or "error" in health_data:
            return "ERROR"
            
        # Simplified logic - in a real implementation, this would have more sophisticated rules
        if health_data.get("database", {}).get("status") == "down":
            return "CRITICAL"
            
        warning_count = sum(1 for component in health_data.values() 
                         if isinstance(component, dict) and component.get("status") == "warning")
                         
        if warning_count > 2:
            return "WARNING"
            
        return "HEALTHY"
