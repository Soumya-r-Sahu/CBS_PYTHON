"""
Standardized Module Interface

This module defines the standard interface that all CBS_PYTHON modules
should implement for consistent integration with the system.

Author: cbs-core-dev
Version: 1.1.2
"""

import logging
import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Callable

# Import service registry
from utils.lib.service_registry import ServiceRegistry

# Configure logger
logger = logging.getLogger(__name__)

class ModuleInterface(ABC):
    """
    Abstract base class defining the standard module interface.
    
    Description:
        This class defines the standard interface that all modules should
        implement for consistent integration with the CBS_PYTHON system.
        It provides methods for initialization, activation, deactivation,
        health checks, and service registration.
    
    Usage:
        class PaymentModule(ModuleInterface):
            def __init__(self):
                super().__init__("payments", "1.0.0")
                # Module-specific initialization
                
            def register_services(self):
                # Register module-specific services
                registry = self.get_registry()
                registry.register("payment.process", self.process_payment, 
                                 version="1.0.0", module_name=self.name)
    """
    
    def __init__(self, name: str, version: str):
        """
        Initialize the module interface
        
        Args:
            name (str): Module name identifier
            version (str): Module version
        """
        self.name = name
        self.version = version
        self.active = False
        self.registry = None
        self.service_registrations = []
        self.dependencies = []
        self.health_status = {
            "status": "initializing",
            "last_check": None,
            "details": {}
        }
        
        logger.info(f"Initializing module {name} v{version}")
    
    def get_registry(self) -> ServiceRegistry:
        """
        Get the service registry instance
        
        Returns:
            ServiceRegistry: The service registry instance
        """
        if self.registry is None:
            self.registry = ServiceRegistry()
        return self.registry
    
    @abstractmethod
    def register_services(self) -> bool:
        """
        Register module services with the service registry
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    def register_dependency(self, module_name: str, required_services: List[str], 
                          is_critical: bool = True) -> None:
        """
        Register a module dependency
        
        Args:
            module_name (str): Name of the required module
            required_services (list): List of required service identifiers
            is_critical (bool): Whether this dependency is critical for operation
        """
        self.dependencies.append({
            "module_name": module_name,
            "required_services": required_services,
            "is_critical": is_critical
        })
        logger.info(f"Module {self.name} registered dependency on {module_name}")
    
    def activate(self) -> bool:
        """
        Activate the module
        
        Returns:
            bool: True if activation was successful
        """
        if self.active:
            logger.info(f"Module {self.name} already active")
            return True
            
        # Check dependencies before activation
        missing_deps = self.check_dependencies()
        if missing_deps and any(dep["is_critical"] for dep in missing_deps):
            logger.error(f"Module {self.name} missing critical dependencies: {missing_deps}")
            return False
            
        try:
            # Register services
            if not self.register_services():
                logger.error(f"Failed to register services for module {self.name}")
                return False
                
            self.active = True
            self.health_status["status"] = "active"
            self.health_status["last_check"] = datetime.datetime.now().isoformat()
            
            logger.info(f"Module {self.name} activated successfully")
            return True
        except Exception as e:
            logger.error(f"Error activating module {self.name}: {str(e)}")
            self.health_status["status"] = "error"
            self.health_status["details"]["error"] = str(e)
            return False
    
    def deactivate(self) -> bool:
        """
        Deactivate the module
        
        Returns:
            bool: True if deactivation was successful
        """
        if not self.active:
            logger.info(f"Module {self.name} already inactive")
            return True
            
        try:
            # Deactivate services in registry
            registry = self.get_registry()
            deactivated = registry.deactivate_module(self.name)
            
            self.active = False
            self.health_status["status"] = "inactive"
            self.health_status["last_check"] = datetime.datetime.now().isoformat()
            
            logger.info(f"Module {self.name} deactivated, services affected: {len(deactivated)}")
            return True
        except Exception as e:
            logger.error(f"Error deactivating module {self.name}: {str(e)}")
            self.health_status["status"] = "error"
            self.health_status["details"]["error"] = str(e)
            return False
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check module health
        
        Returns:
            dict: Health status information
        """
        try:
            # Perform health check
            health_details = self._perform_health_check()
            
            # Update status
            self.health_status["status"] = "active" if self.active else "inactive"
            self.health_status["last_check"] = datetime.datetime.now().isoformat()
            self.health_status["details"] = health_details
            
            return self.health_status
        except Exception as e:
            logger.error(f"Error checking health for module {self.name}: {str(e)}")
            self.health_status["status"] = "error"
            self.health_status["details"]["error"] = str(e)
            return self.health_status
    
    def _perform_health_check(self) -> Dict[str, Any]:
        """
        Perform module-specific health checks
        
        Returns:
            dict: Health check details
        """
        # Default implementation checks dependencies
        missing_deps = self.check_dependencies()
        
        return {
            "dependencies_met": not any(dep["is_critical"] for dep in missing_deps),
            "missing_dependencies": missing_deps,
            "services_registered": len(self.service_registrations)
        }
    
    def check_dependencies(self) -> List[Dict[str, Any]]:
        """
        Check if all dependencies are available
        
        Returns:
            list: List of missing dependencies
        """
        missing = []
        registry = self.get_registry()
        
        for dep in self.dependencies:
            module_name = dep["module_name"]
            missing_services = []
            
            for service_name in dep["required_services"]:
                service = registry.get_service(service_name)
                if service is None:
                    missing_services.append(service_name)
            
            if missing_services:
                missing.append({
                    "module_name": module_name,
                    "missing_services": missing_services,
                    "is_critical": dep["is_critical"]
                })
        
        return missing
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get module information
        
        Returns:
            dict: Module information
        """
        return {
            "name": self.name,
            "version": self.version,
            "active": self.active,
            "health_status": self.health_status["status"],
            "dependencies": len(self.dependencies),
            "registered_services": len(self.service_registrations)
        }

class ModuleRegistry:
    """
    Registry for module instances
    
    Description:
        This class provides a registry for module instances, allowing the
        system to manage and orchestrate modules. It supports activating,
        deactivating, and checking health across all registered modules.
    
    Usage:
        # Get registry instance
        registry = ModuleRegistry.get_instance()
        
        # Register module
        registry.register_module(PaymentModule())
        
        # Activate all modules
        registry.activate_all()
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance
        
        Returns:
            ModuleRegistry: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize the module registry"""
        self.modules = {}
        logger.info("Module registry initialized")
    
    def register_module(self, module: ModuleInterface) -> bool:
        """
        Register a module
        
        Args:
            module (ModuleInterface): Module instance to register
            
        Returns:
            bool: True if registration was successful
        """
        if module.name in self.modules:
            logger.warning(f"Module {module.name} already registered, replacing")
            
        self.modules[module.name] = module
        logger.info(f"Module {module.name} v{module.version} registered")
        return True
    
    def get_module(self, name: str) -> Optional[ModuleInterface]:
        """
        Get a module by name
        
        Args:
            name (str): Module name
            
        Returns:
            ModuleInterface: The module instance or None if not found
        """
        return self.modules.get(name)
    
    def list_modules(self) -> List[Dict[str, Any]]:
        """
        List all registered modules
        
        Returns:
            list: List of module information dictionaries
        """
        return [module.get_info() for module in self.modules.values()]
    
    def activate_module(self, name: str) -> bool:
        """
        Activate a specific module
        
        Args:
            name (str): Module name
            
        Returns:
            bool: True if activation was successful
        """
        module = self.modules.get(name)
        if not module:
            logger.error(f"Module {name} not found")
            return False
            
        return module.activate()
    
    def deactivate_module(self, name: str) -> bool:
        """
        Deactivate a specific module
        
        Args:
            name (str): Module name
            
        Returns:
            bool: True if deactivation was successful
        """
        module = self.modules.get(name)
        if not module:
            logger.error(f"Module {name} not found")
            return False
            
        return module.deactivate()
    
    def activate_all(self) -> Dict[str, bool]:
        """
        Activate all modules
        
        Returns:
            dict: Results of activation by module name
        """
        results = {}
        
        # First activate modules with no dependencies
        for name, module in self.modules.items():
            if not module.dependencies:
                results[name] = module.activate()
        
        # Then activate the rest
        for name, module in self.modules.items():
            if name not in results:
                results[name] = module.activate()
        
        return results
    
    def deactivate_all(self) -> Dict[str, bool]:
        """
        Deactivate all modules
        
        Returns:
            dict: Results of deactivation by module name
        """
        results = {}
        
        # Deactivate in reverse order of dependency
        for name, module in self.modules.items():
            results[name] = module.deactivate()
        
        return results
    
    def check_health_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Check health of all modules
        
        Returns:
            dict: Health status by module name
        """
        results = {}
        
        for name, module in self.modules.items():
            results[name] = module.check_health()
        
        return results
