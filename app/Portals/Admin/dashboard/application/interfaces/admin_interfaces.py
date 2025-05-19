"""
Admin Application Layer Interfaces

This module defines the application layer interfaces for the Admin module.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from dashboard.domain.entities.admin_entities import Module, ApiEndpoint, FeatureFlag

class ModuleRepository(ABC):
    """Repository interface for Module entities"""
    
    @abstractmethod
    def get_all_modules(self) -> List[Module]:
        """Retrieve all modules in the system"""
        pass
    
    @abstractmethod
    def get_module_by_id(self, module_id: str) -> Optional[Module]:
        """Retrieve a module by its ID"""
        pass
    
    @abstractmethod
    def update_module(self, module: Module) -> Module:
        """Update a module"""
        pass
    
    @abstractmethod
    def toggle_module_status(self, module_id: str, active: bool) -> Module:
        """Toggle a module's active status"""
        pass

class ApiEndpointRepository(ABC):
    """Repository interface for ApiEndpoint entities"""
    
    @abstractmethod
    def get_all_endpoints(self) -> List[ApiEndpoint]:
        """Retrieve all API endpoints"""
        pass
    
    @abstractmethod
    def get_endpoints_by_module(self, module_id: str) -> List[ApiEndpoint]:
        """Retrieve all API endpoints for a specific module"""
        pass
    
    @abstractmethod
    def update_endpoint(self, endpoint: ApiEndpoint) -> ApiEndpoint:
        """Update an API endpoint"""
        pass
    
    @abstractmethod
    def toggle_endpoint(self, endpoint_id: str, enabled: bool) -> ApiEndpoint:
        """Toggle an API endpoint's enabled status"""
        pass

class FeatureFlagRepository(ABC):
    """Repository interface for FeatureFlag entities"""
    
    @abstractmethod
    def get_all_features(self) -> List[FeatureFlag]:
        """Retrieve all feature flags"""
        pass
    
    @abstractmethod
    def get_features_by_module(self, module_id: str) -> List[FeatureFlag]:
        """Retrieve all feature flags for a specific module"""
        pass
    
    @abstractmethod
    def update_feature(self, feature: FeatureFlag) -> FeatureFlag:
        """Update a feature flag"""
        pass
    
    @abstractmethod
    def toggle_feature(self, feature_name: str, module_id: str, enabled: bool) -> FeatureFlag:
        """Toggle a feature flag's enabled status"""
        pass

class SystemMonitoringService(ABC):
    """Service interface for system monitoring"""
    
    @abstractmethod
    def get_system_health(self) -> Dict[str, Any]:
        """Get the overall system health"""
        pass
    
    @abstractmethod
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get system resource usage"""
        pass
