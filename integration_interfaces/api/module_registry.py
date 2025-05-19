"""
Module Registry Interface

This module defines the interface that all CBS modules should implement
to register with the Admin module.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class ModuleRegistryInterface(ABC):
    """Interface for module registration with the Admin system."""
    
    @abstractmethod
    def get_module_info(self) -> Dict[str, Any]:
        """
        Get basic information about the module.
        
        Returns:
            Dict containing:
                - id: Unique identifier for the module
                - name: Display name of the module
                - version: Version string
                - description: Brief description of the module
                - dependencies: List of module IDs this module depends on
        """
        pass
    
    @abstractmethod
    def get_api_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get all API endpoints exposed by this module.
        
        Returns:
            List of dictionaries, each containing:
                - path: URL path of the endpoint
                - method: HTTP method (GET, POST, etc.)
                - description: Brief description of what the endpoint does
                - auth_required: Whether authentication is required
                - rate_limit: Optional rate limit in requests per minute
        """
        pass
    
    @abstractmethod
    def get_feature_flags(self) -> List[Dict[str, Any]]:
        """
        Get all feature flags defined by this module.
        
        Returns:
            List of dictionaries, each containing:
                - name: Feature flag name
                - description: Description of the feature
                - enabled: Default enabled state
                - affects_endpoints: List of endpoint IDs affected by this flag
        """
        pass
    
    @abstractmethod
    def get_configurations(self) -> List[Dict[str, Any]]:
        """
        Get all configurable settings for this module.
        
        Returns:
            List of dictionaries, each containing:
                - key: Configuration key
                - value: Default value
                - type: Type of configuration (system, module, api, feature, security, performance)
                - description: Description of the configuration
                - is_sensitive: Whether this is sensitive data (passwords, etc.)
                - allowed_values: Optional list of allowed values
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check for this module.
        
        Returns:
            Dictionary containing:
                - status: One of "healthy", "warning", "critical", "unknown"
                - metrics: Dictionary of metrics (CPU, memory, etc.)
                - details: Additional details about the health check
                - alerts: List of alert messages if any
        """
        pass
