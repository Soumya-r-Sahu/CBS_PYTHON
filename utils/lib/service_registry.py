"""
Service Registry for CBS_PYTHON

This module provides a service registry pattern for module services.
Enables loose coupling between modules and their dependencies.

Author: cbs-core-dev
Version: 1.1.2
"""

import logging
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """
    Service registry for module services.
    Enables loose coupling between modules and their dependencies.
    
    Description:
        The ServiceRegistry implements a singleton pattern to provide
        a central location for registering and discovering services across
        modules. It supports versioning, fallback behaviors for graceful
        degradation, and module activation/deactivation.
    
    Usage:
        # Register a service
        registry = ServiceRegistry.get_instance()
        registry.register("payment.processor", PaymentProcessor(), "1.0.0", "payments")
        
        # Register a fallback
        registry.register_fallback("payment.processor", BasicPaymentProcessor())
        
        # Get a service
        payment_service = registry.get_service("payment.processor")
        
        # Deactivate a module's services
        registry.deactivate_module("payments")
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the registry's internal state."""
        self.services = {}
        self.fallbacks = {}
        self.modules = {}
        logger.debug("Service Registry initialized")
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of the service registry
        
        Returns:
            ServiceRegistry: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register(self, service_name: str, implementation: Any, version: str = '1.0.0', 
                 module_name: Optional[str] = None) -> bool:
        """
        Register a service implementation
        
        Args:
            service_name (str): Unique name of the service
            implementation (object): The service implementation
            version (str): Service implementation version
            module_name (str, optional): Name of the providing module
            
        Returns:
            bool: True if registration was successful
        """
        try:
            if service_name not in self.services:
                self.services[service_name] = {}
            
            self.services[service_name][version] = {
                'implementation': implementation,
                'module_name': module_name,
                'active': True
            }
            
            # Track module services
            if module_name:
                if module_name not in self.modules:
                    self.modules[module_name] = []
                self.modules[module_name].append(service_name)
                
            logger.debug(f"Registered service '{service_name}' v{version} from module '{module_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to register service '{service_name}': {str(e)}")
            return False
    
    def get_service(self, service_name: str, version: str = 'latest') -> Optional[Any]:
        """
        Get a service by name and optional version
        
        Args:
            service_name (str): Service name to look up
            version (str): Service version (or 'latest' for most recent)
        
        Returns:
            The service implementation or fallback, or None if not found
        """
        try:
            if service_name not in self.services:
                # Check for fallback implementation
                if service_name in self.fallbacks:
                    logger.debug(f"Using fallback for service '{service_name}'")
                    return self.fallbacks[service_name]
                logger.debug(f"Service '{service_name}' not found")
                return None
            
            if version == 'latest':
                # Return the latest version (assuming semantic versioning)
                versions = list(self.services[service_name].keys())
                if not versions:
                    logger.debug(f"No versions found for service '{service_name}'")
                    return None
                    
                latest = sorted(versions, key=lambda v: [int(x) for x in v.split('.')])[-1]
                service_info = self.services[service_name][latest]
            else:
                # Return specific version if available
                if version not in self.services[service_name]:
                    logger.debug(f"Version '{version}' not found for service '{service_name}'")
                    return None
                service_info = self.services[service_name][version]
            
            # Check if the service is active
            if not service_info['active']:
                # Check for fallback implementation
                if service_name in self.fallbacks:
                    logger.debug(f"Using fallback for inactive service '{service_name}'")
                    return self.fallbacks[service_name]
                logger.debug(f"Service '{service_name}' is not active")
                return None
                
            return service_info['implementation']
        except Exception as e:
            logger.error(f"Error retrieving service '{service_name}': {str(e)}")
            # Return fallback if available
            if service_name in self.fallbacks:
                logger.debug(f"Using fallback after error for service '{service_name}'")
                return self.fallbacks[service_name]
            return None

    def register_fallback(self, service_name: str, implementation: Any) -> bool:
        """
        Register a fallback implementation for a service
        
        Args:
            service_name (str): Service name to register fallback for
            implementation (object): The fallback implementation
            
        Returns:
            bool: True if registration was successful
        """
        try:
            self.fallbacks[service_name] = implementation
            logger.debug(f"Registered fallback for service '{service_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to register fallback for service '{service_name}': {str(e)}")
            return False
    
    def activate_service(self, service_name: str, version: str = 'all') -> bool:
        """
        Activate a service
        
        Args:
            service_name (str): Service name to activate
            version (str): Service version, or 'all' for all versions
            
        Returns:
            bool: True if activation was successful
        """
        try:
            if service_name not in self.services:
                logger.debug(f"Service '{service_name}' not found")
                return False
                
            if version == 'all':
                # Activate all versions
                for ver in self.services[service_name]:
                    self.services[service_name][ver]['active'] = True
                logger.debug(f"Activated all versions of service '{service_name}'")
            else:
                # Activate specific version
                if version not in self.services[service_name]:
                    logger.debug(f"Version '{version}' not found for service '{service_name}'")
                    return False
                self.services[service_name][version]['active'] = True
                logger.debug(f"Activated service '{service_name}' v{version}")
                
            return True
        except Exception as e:
            logger.error(f"Failed to activate service '{service_name}': {str(e)}")
            return False
    
    def deactivate_service(self, service_name: str, version: str = 'all') -> bool:
        """
        Deactivate a service
        
        Args:
            service_name (str): Service name to deactivate
            version (str): Service version, or 'all' for all versions
            
        Returns:
            bool: True if deactivation was successful
        """
        try:
            if service_name not in self.services:
                logger.debug(f"Service '{service_name}' not found")
                return False
                
            if version == 'all':
                # Deactivate all versions
                for ver in self.services[service_name]:
                    self.services[service_name][ver]['active'] = False
                logger.debug(f"Deactivated all versions of service '{service_name}'")
            else:
                # Deactivate specific version
                if version not in self.services[service_name]:
                    logger.debug(f"Version '{version}' not found for service '{service_name}'")
                    return False
                self.services[service_name][version]['active'] = False
                logger.debug(f"Deactivated service '{service_name}' v{version}")
                
            return True
        except Exception as e:
            logger.error(f"Failed to deactivate service '{service_name}': {str(e)}")
            return False
    
    def deactivate_module(self, module_name: str) -> bool:
        """
        Deactivate all services from a module
        
        Args:
            module_name (str): Module name to deactivate
            
        Returns:
            bool: True if deactivation was successful
        """
        try:
            if module_name not in self.modules:
                logger.debug(f"Module '{module_name}' not found")
                return False
                
            success = True
            for service_name in self.modules[module_name]:
                if not self.deactivate_service(service_name, 'all'):
                    success = False
                    
            if success:
                logger.debug(f"Deactivated all services from module '{module_name}'")
            else:
                logger.warning(f"Some services from module '{module_name}' could not be deactivated")
                
            return success
        except Exception as e:
            logger.error(f"Failed to deactivate module '{module_name}': {str(e)}")
            return False
            
    def list_services(self) -> Dict[str, List[str]]:
        """
        List all registered services
        
        Returns:
            dict: Dictionary mapping service names to lists of available versions
        """
        result = {}
        for service_name, versions in self.services.items():
            active_versions = []
            for version, info in versions.items():
                if info['active']:
                    active_versions.append(version)
            if active_versions:
                result[service_name] = active_versions
        return result
        
    def list_all_services(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered services, including inactive ones
        
        Returns:
            dict: Dictionary mapping service names to service information
        """
        return {
            service_name: {
                "versions": list(versions.keys()),
                "module": next((info["module_name"] for info in versions.values() 
                              if info["module_name"]), None)
            }
            for service_name, versions in self.services.items()
        }
