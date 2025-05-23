"""
Core Banking Module Interface Implementation

This module implements the standardized module interface for the core banking module.

Author: cbs-core-dev
Version: 1.3.0
"""

import logging
import importlib
from typing import Dict, List, Any, Optional, Tuple

# Import the module interface
from utils.lib.module_interface import ModuleInterface
from utils.lib.service_registry import ServiceRegistry

# Configure logger
logger = logging.getLogger(__name__)

class CoreBankingModule(ModuleInterface):
    """
    Core Banking module implementation
    
    Description:
        This class implements the standardized module interface for the
        core banking module, providing essential banking capabilities to
        the CBS_PYTHON system.
    """
    
    def __init__(self):
        """Initialize the core banking module"""
        super().__init__("core_banking", "1.3.0")
        
        # Define module-specific attributes
        self.supported_account_types = ["savings", "checking", "loan", "term_deposit", "credit"]
        
        # Register dependencies
        self.register_dependency("database", ["database.operations"], is_critical=True)
        self.register_dependency("security", ["security.operations"], is_critical=True)
        
        # Cache for module imports and services
        self._module_cache = {}
        self._service_implementations = {}
        
        logger.info(f"{self.name} module initialized")
    
    def _import_module(self, module_path: str) -> Optional[object]:
        """
        Safely import a module and cache it
        
        Args:
            module_path: The import path of the module
            
        Returns:
            The imported module or None if import failed
        """
        if module_path in self._module_cache:
            return self._module_cache[module_path]
            
        try:
            module = importlib.import_module(module_path)
            self._module_cache[module_path] = module
            return module
        except ImportError as e:
            logger.warning(f"Failed to import {module_path}: {str(e)}")
            return None
    
    def _get_service_implementation(self, service_name: str) -> Tuple[Optional[object], str]:
        """
        Get a service implementation, trying multiple paths
        
        Args:
            service_name: The name of the service to get (e.g., 'accounts.create')
            
        Returns:
            Tuple of (implementation, source) where source is a string describing where
            the implementation was found, or (None, error_message) if not found
        """
        # Check if we've already resolved this service
        if service_name in self._service_implementations:
            return self._service_implementations[service_name]
        
        # Try to get from this class first (fastest path)
        if hasattr(self, service_name.split('.')[-1]):
            impl = getattr(self, service_name.split('.')[-1])
            self._service_implementations[service_name] = (impl, "local")
            return impl, "local"
        
        # Try direct import path based on service name
        components = service_name.split('.')
        if len(components) >= 2:
            # Try core_banking.{service_category}.{service_name}
            module_path = f"core_banking.{components[0]}"
            module = self._import_module(module_path)
            
            if module and hasattr(module, components[1]):
                impl = getattr(module, components[1])
                self._service_implementations[service_name] = (impl, module_path)
                return impl, module_path
            
            # Try core_banking.{service_category}.services.{service_name}
            module_path = f"core_banking.{components[0]}.services"
            module = self._import_module(module_path)
            
            if module and hasattr(module, components[1]):
                impl = getattr(module, components[1])
                self._service_implementations[service_name] = (impl, module_path)
                return impl, module_path
        
        # Service not found
        self._service_implementations[service_name] = (None, f"Service {service_name} not found")
        return None, f"Service {service_name} not found"
    
    def register_services(self) -> bool:
        """
        Register core banking services with the service registry
        
        Returns:
            bool: True if registration was successful
        """
        try:
            registry = self.get_registry()
            services_count = 0
            
            # Define all the services to register
            services = [
                # Account services
                ("accounts.create", self.create_account),
                ("accounts.get_account", self.get_account_details),
                ("accounts.update", self.update_account),
                ("accounts.close", self.close_account),
                ("accounts.get_balance", self.get_account_balance),
                ("accounts.freeze", self.freeze_account),
                ("accounts.unfreeze", self.unfreeze_account),
                
                # Transaction services
                ("transactions.post", self.post_transaction),
                ("transactions.reverse", self.reverse_transaction),
                ("transactions.get_history", self.get_transaction_history),
                
                # Interest services
                ("interest.calculate", self.calculate_interest),
                ("interest.post", self.post_interest),
                
                # Module services
                (f"{self.name}.health.check", self.check_health),
                (f"{self.name}.info", self.get_info)
            ]
            
            # Register all services
            for service_name, implementation in services:
                if registry.register(service_name, implementation, version="1.0.0", module_name=self.name):
                    services_count += 1
                    logger.debug(f"Registered service {service_name}")
            
            logger.info(f"Registered {services_count} {self.name} module services")
            return services_count > 0
        except Exception as e:
            logger.error(f"Failed to register {self.name} module services: {str(e)}")
            return False

# Function to get module instance
def get_module_instance():
    """Get an instance of the Core Banking module"""
    return CoreBankingModule()
