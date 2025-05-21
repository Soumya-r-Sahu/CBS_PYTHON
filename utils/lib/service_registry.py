"""
Service Registry for CBS_PYTHON

This module provides a service registry pattern for module services.
Enables loose coupling between modules and their dependencies.

Author: cbs-core-dev
Version: 1.1.2
"""

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
        registry = ServiceRegistry()
        registry.register("payment.processor", PaymentProcessor(), "1.0.0", "payments")
        
        # Register a fallback
        registry.register_fallback("payment.processor", BasicPaymentProcessor())
        
        # Get a service
        payment_service = registry.get_service("payment.processor")
        
        # Deactivate a module's services
        registry.deactivate_module("payments")    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
            cls._instance.services = {}
            cls._instance.fallbacks = {}
        return cls._instance
    
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
    
    def register(self, service_name, implementation, version='1.0.0', module_name=None):
        """
        Register a service implementation
        
        Args:
            service_name (str): Unique name of the service
            implementation (object): The service implementation
            version (str): Service implementation version
            module_name (str, optional): Name of the providing module
        """
        if service_name not in self.services:
            self.services[service_name] = {}
        
        self.services[service_name][version] = {
            'implementation': implementation,
            'module_name': module_name,
            'active': True
        }
    
    def get_service(self, service_name, version='latest'):
        """
        Get a service by name and optional version
        
        Args:
            service_name (str): Service name to look up
            version (str): Service version (or 'latest' for most recent)
        
        Returns:
            The service implementation or fallback, or None if not found
        """
        if service_name not in self.services:
            # Check for fallback implementation
            if service_name in self.fallbacks:
                return self.fallbacks[service_name]
            return None
        
        if version == 'latest':
            # Return the latest version (assuming semantic versioning)
            versions = list(self.services[service_name].keys())
            if not versions:
                return None
            latest = sorted(versions, key=lambda v: [int(x) for x in v.split('.')])[-1]
            service_info = self.services[service_name][latest]
        else:
            # Return specific version if available
            if version not in self.services[service_name]:
                return None
            service_info = self.services[service_name][version]
        
        # Check if service is active
        if service_info['active']:
            return service_info['implementation']
        
        # Return fallback if available
        if service_name in self.fallbacks:
            return self.fallbacks[service_name]
        
        return None
    
    def register_fallback(self, service_name, implementation):
        """
        Register a fallback implementation for a service
        Used when the primary implementation is unavailable
        
        Args:
            service_name (str): Service name
            implementation (object): Fallback implementation
        """
        self.fallbacks[service_name] = implementation
    
    def unregister(self, service_name, version=None):
        """
        Unregister a service or specific version
        
        Args:
            service_name (str): Service name
            version (str, optional): Specific version to unregister
        
        Returns:
            bool: True if successful, False otherwise
        """
        if service_name not in self.services:
            return False
        
        if version is None:
            # Remove all versions
            del self.services[service_name]
            return True
        elif version in self.services[service_name]:
            # Remove specific version
            del self.services[service_name][version]
            return True
        
        return False
    
    def deactivate_module(self, module_name):
        """
        Deactivate all services from a module
        
        Args:
            module_name (str): Module name to deactivate
            
        Returns:
            list: List of deactivated service names
        """
        deactivated = []
        
        for service_name, versions in self.services.items():
            for version, service_info in versions.items():
                if service_info.get('module_name') == module_name and service_info['active']:
                    service_info['active'] = False
                    deactivated.append(f"{service_name}@{version}")
        
        return deactivated
                
    def activate_module(self, module_name):
        """
        Activate all services from a module
        
        Args:
            module_name (str): Module name to activate
            
        Returns:
            list: List of activated service names
        """
        activated = []
        
        for service_name, versions in self.services.items():
            for version, service_info in versions.items():
                if service_info.get('module_name') == module_name and not service_info['active']:
                    service_info['active'] = True
                    activated.append(f"{service_name}@{version}")
        
        return activated
    
    def list_services(self):
        """
        List all registered services
        
        Returns:
            list: List of dictionaries containing service information
        """
        result = []
        
        for service_name, versions in self.services.items():
            for version, service_info in versions.items():
                result.append({
                    'name': service_name,
                    'version': version,
                    'module': service_info.get('module_name', 'unknown'),
                    'active': service_info['active'],
                    'implementation': service_info['implementation'].__class__.__name__
                })
        
        return result
    
    def list_fallbacks(self):
        """
        List all registered fallbacks
        
        Returns:
            list: List of dictionaries containing fallback information
        """
        result = []
        
        for service_name, implementation in self.fallbacks.items():
            result.append({
                'name': service_name,
                'implementation': implementation.__class__.__name__
            })
        
        return result

    def list_all_services(self):
        """
        List all registered services (for backward compatibility)
        
        Returns:
            list: List of all registered service names
        """
        return [service['name'] for service in self.list_services()]
