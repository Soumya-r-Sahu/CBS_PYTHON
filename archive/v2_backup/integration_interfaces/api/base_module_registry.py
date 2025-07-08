"""
Base Module Registry Implementation

This module provides a base implementation of the Module Registry Interface
that can be extended by individual modules.
"""
from typing import Dict, List, Any, Optional
from integration_interfaces.api.module_registry import ModuleRegistryInterface


class BaseModuleRegistry(ModuleRegistryInterface):
    """Base implementation of the Module Registry Interface."""
    
    def __init__(self, module_id: str, module_name: str, version: str, description: str = None):
        """
        Initialize the base module registry.
        
        Args:
            module_id: Unique identifier for the module
            module_name: Display name of the module
            version: Version string
            description: Brief description of the module
        """
        self.module_id = module_id
        self.module_name = module_name
        self.version = version
        self.description = description or f"{module_name} module for CBS"
        self.dependencies = []
    
    def get_module_info(self) -> Dict[str, Any]:
        """
        Get basic information about the module.
        
        Returns:
            Dictionary containing module information
        """
        return {
            "id": self.module_id,
            "name": self.module_name,
            "version": self.version,
            "description": self.description,
            "dependencies": self.dependencies
        }
    
    def set_dependencies(self, dependencies: List[str]) -> None:
        """
        Set the module dependencies.
        
        Args:
            dependencies: List of module IDs this module depends on
        """
        self.dependencies = dependencies
    
    def get_api_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get all API endpoints exposed by this module.
        
        Should be overridden by subclasses.
        
        Returns:
            Empty list by default
        """
        return []
    
    def get_feature_flags(self) -> List[Dict[str, Any]]:
        """
        Get all feature flags defined by this module.
        
        Should be overridden by subclasses.
        
        Returns:
            Empty list by default
        """
        return []
    
    def get_configurations(self) -> List[Dict[str, Any]]:
        """
        Get all configurable settings for this module.
        
        Should be overridden by subclasses.
        
        Returns:
            Empty list by default
        """
        return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check for this module.
        
        Should be overridden by subclasses.
        
        Returns:
            Dictionary with "unknown" status by default
        """
        return {
            "status": "unknown",
            "metrics": {},
            "details": {"message": "No health check implemented"},
            "alerts": []
        }
