"""
Admin Infrastructure Repositories

This module implements the infrastructure layer repositories for the Admin module.
"""

import logging
import os
import json
from typing import List, Optional, Dict, Any
import psutil

from dashboard.domain.entities.admin_entities import Module, ApiEndpoint, FeatureFlag, ModuleStatus
from dashboard.application.interfaces.admin_interfaces import (
    ModuleRepository, 
    ApiEndpointRepository,
    FeatureFlagRepository,
    SystemMonitoringService
)

logger = logging.getLogger(__name__)

class InMemoryModuleRepository(ModuleRepository):
    """In-memory implementation of ModuleRepository"""
    
    def __init__(self):
        self.modules = self._load_modules()
    
    def _load_modules(self) -> Dict[str, Module]:
        """Load modules from the system - this would typically check installed modules"""
        modules = {}
        
        # In a real implementation, this would scan the file system or database
        # For now, we'll use hardcoded sample data
        core_banking = Module(
            id="core_banking",
            name="Core Banking",
            version="1.0.0",
            status=ModuleStatus.ACTIVE,
            dependencies=[]
        )
        
        payments = Module(
            id="payments",
            name="Payments",
            version="1.0.0",
            status=ModuleStatus.ACTIVE,
            dependencies=["core_banking"]
        )
        
        digital_channels = Module(
            id="digital_channels",
            name="Digital Channels",
            version="0.9.0",
            status=ModuleStatus.ACTIVE,
            dependencies=["core_banking", "payments"]
        )
        
        treasury = Module(
            id="treasury",
            name="Treasury",
            version="0.8.5",
            status=ModuleStatus.ACTIVE,
            dependencies=["core_banking"]
        )
        
        modules = {
            "core_banking": core_banking,
            "payments": payments,
            "digital_channels": digital_channels,
            "treasury": treasury
        }
        
        return modules
    
    def get_all_modules(self) -> List[Module]:
        """Get all modules"""
        return list(self.modules.values())
    
    def get_module_by_id(self, module_id: str) -> Optional[Module]:
        """Get a module by ID"""
        return self.modules.get(module_id)
    
    def update_module(self, module: Module) -> Module:
        """Update a module"""
        self.modules[module.id] = module
        return module
    
    def toggle_module_status(self, module_id: str, active: bool) -> Module:
        """Toggle a module's active status"""
        module = self.get_module_by_id(module_id)
        if not module:
            raise ValueError(f"Module not found: {module_id}")
        
        if active:
            module.status = ModuleStatus.ACTIVE
        else:
            module.status = ModuleStatus.DEACTIVATED
        
        self.modules[module_id] = module
        return module

class InMemoryApiEndpointRepository(ApiEndpointRepository):
    """In-memory implementation of ApiEndpointRepository"""
    
    def __init__(self):
        self.endpoints = self._load_endpoints()
    
    def _load_endpoints(self) -> Dict[str, ApiEndpoint]:
        """Load API endpoints - this would typically come from routing configuration"""
        endpoints = {}
        
        # Core Banking endpoints
        endpoints["core_accounts_get"] = ApiEndpoint(
            id="core_accounts_get",
            path="/api/v1/accounts",
            module_id="core_banking",
            method="GET",
            enabled=True,
            rate_limit=100,
            auth_required=True
        )
        
        endpoints["core_account_details"] = ApiEndpoint(
            id="core_account_details",
            path="/api/v1/accounts/{id}",
            module_id="core_banking",
            method="GET",
            enabled=True,
            rate_limit=100,
            auth_required=True
        )
        
        # Payments endpoints
        endpoints["payments_initiate"] = ApiEndpoint(
            id="payments_initiate",
            path="/api/v1/payments",
            module_id="payments",
            method="POST",
            enabled=True,
            rate_limit=50,
            auth_required=True
        )
        
        endpoints["payments_status"] = ApiEndpoint(
            id="payments_status",
            path="/api/v1/payments/{id}",
            module_id="payments",
            method="GET",
            enabled=True,
            rate_limit=100,
            auth_required=True
        )
        
        return endpoints
    
    def get_all_endpoints(self) -> List[ApiEndpoint]:
        """Get all API endpoints"""
        return list(self.endpoints.values())
    
    def get_endpoints_by_module(self, module_id: str) -> List[ApiEndpoint]:
        """Get endpoints for a specific module"""
        return [endpoint for endpoint in self.endpoints.values() if endpoint.module_id == module_id]
    
    def update_endpoint(self, endpoint: ApiEndpoint) -> ApiEndpoint:
        """Update an API endpoint"""
        self.endpoints[endpoint.id] = endpoint
        return endpoint
    
    def toggle_endpoint(self, endpoint_id: str, enabled: bool) -> ApiEndpoint:
        """Toggle an endpoint's enabled status"""
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint not found: {endpoint_id}")
        
        endpoint.enabled = enabled
        self.endpoints[endpoint_id] = endpoint
        return endpoint

class InMemoryFeatureFlagRepository(FeatureFlagRepository):
    """In-memory implementation of FeatureFlagRepository"""
    
    def __init__(self):
        self.features = self._load_features()
    
    def _load_features(self) -> Dict[str, FeatureFlag]:
        """Load feature flags - this would typically come from a configuration store"""
        features = {}
        
        # Core Banking features
        features["core_banking:multi_currency"] = FeatureFlag(
            name="multi_currency",
            description="Enable multi-currency accounts",
            enabled=True,
            module_id="core_banking",
            affects_endpoints=["core_accounts_get", "core_account_details"]
        )
        
        # Payments features
        features["payments:instant_transfer"] = FeatureFlag(
            name="instant_transfer",
            description="Enable instant transfers",
            enabled=True,
            module_id="payments",
            affects_endpoints=["payments_initiate"]
        )
        
        features["payments:scheduled_payments"] = FeatureFlag(
            name="scheduled_payments",
            description="Enable scheduled payments",
            enabled=False,
            module_id="payments",
            affects_endpoints=["payments_initiate"]
        )
        
        return features
    
    def get_all_features(self) -> List[FeatureFlag]:
        """Get all feature flags"""
        return list(self.features.values())
    
    def get_features_by_module(self, module_id: str) -> List[FeatureFlag]:
        """Get features for a specific module"""
        return [feature for feature in self.features.values() if feature.module_id == module_id]
    
    def update_feature(self, feature: FeatureFlag) -> FeatureFlag:
        """Update a feature flag"""
        key = f"{feature.module_id}:{feature.name}"
        self.features[key] = feature
        return feature
    
    def toggle_feature(self, feature_name: str, module_id: str, enabled: bool) -> FeatureFlag:
        """Toggle a feature flag's enabled status"""
        key = f"{module_id}:{feature_name}"
        feature = self.features.get(key)
        if not feature:
            raise ValueError(f"Feature not found: {key}")
        
        feature.enabled = enabled
        self.features[key] = feature
        return feature

class PsutilSystemMonitoringService(SystemMonitoringService):
    """System monitoring implementation using psutil"""
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health information"""
        try:
            health = {
                "database": self._check_database_health(),
                "disk": self._check_disk_health(),
                "memory": self._check_memory_health(),
                "cpu": self._check_cpu_health()
            }
            return health
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {"error": str(e)}
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get system resource usage"""
        try:
            usage = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                }
            }
            return usage
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {"error": str(e)}
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database health - this would typically connect to the database"""
        # In a real implementation, this would check the database connection
        return {"status": "up", "latency_ms": 5}
    
    def _check_disk_health(self) -> Dict[str, Any]:
        """Check disk health"""
        usage = psutil.disk_usage('/')
        status = "healthy"
        if usage.percent > 90:
            status = "warning"
        if usage.percent > 95:
            status = "critical"
        
        return {"status": status, "usage_percent": usage.percent}
    
    def _check_memory_health(self) -> Dict[str, Any]:
        """Check memory health"""
        memory = psutil.virtual_memory()
        status = "healthy"
        if memory.percent > 80:
            status = "warning"
        if memory.percent > 90:
            status = "critical"
        
        return {"status": status, "usage_percent": memory.percent}
    
    def _check_cpu_health(self) -> Dict[str, Any]:
        """Check CPU health"""
        cpu_percent = psutil.cpu_percent(interval=1)
        status = "healthy"
        if cpu_percent > 70:
            status = "warning"
        if cpu_percent > 90:
            status = "critical"
        
        return {"status": status, "usage_percent": cpu_percent}
