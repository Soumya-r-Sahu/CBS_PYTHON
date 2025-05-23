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
            self.registry = ServiceRegistry.get_instance()
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
        
        logger.debug(f"Module {self.name} registered dependency on {module_name}")
    
    def activate(self) -> bool:
        """
        Activate the module
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Activating module {self.name} v{self.version}")
            # Register services with the service registry
            if not self.register_services():
                logger.error(f"Failed to register services for module {self.name}")
                return False
                
            # Set module as active
            self.active = True
            self.health_status["status"] = "active"
            self.health_status["last_check"] = datetime.datetime.now().isoformat()
            
            logger.info(f"Module {self.name} v{self.version} activated successfully")
            return True
        except Exception as e:
            logger.error(f"Error activating module {self.name}: {str(e)}")
            self.health_status["status"] = "error"
            self.health_status["last_check"] = datetime.datetime.now().isoformat()
            self.health_status["details"]["activation_error"] = str(e)
            return False
    
    def deactivate(self) -> bool:
        """
        Deactivate the module
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Deactivating module {self.name}")
            
            # Deactivate all services from this module
            registry = self.get_registry()
            success = registry.deactivate_module(self.name)
            
            if success:
                self.active = False
                self.health_status["status"] = "inactive"
                self.health_status["last_check"] = datetime.datetime.now().isoformat()
                logger.info(f"Module {self.name} deactivated successfully")
            else:
                logger.error(f"Failed to deactivate module {self.name}")
                self.health_status["status"] = "error"
                self.health_status["last_check"] = datetime.datetime.now().isoformat()
                self.health_status["details"]["deactivation_error"] = "Failed to deactivate module services"
            
            return success
        except Exception as e:
            logger.error(f"Error deactivating module {self.name}: {str(e)}")
            self.health_status["status"] = "error"
            self.health_status["last_check"] = datetime.datetime.now().isoformat()
            self.health_status["details"]["deactivation_error"] = str(e)
            return False
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check module health status
        
        Returns:
            dict: Health status information
        """
        try:
            logger.debug(f"Checking health for module {self.name}")
            
            # Update the timestamp
            self.health_status["last_check"] = datetime.datetime.now().isoformat()
            
            # Check dependencies health
            dependency_status = self.check_dependencies()
            self.health_status["details"]["dependencies"] = dependency_status
            
            # Update overall status based on dependency health
            if not self.active:
                self.health_status["status"] = "inactive"
            elif any(dep["status"] == "error" for dep in dependency_status if dep["is_critical"]):
                self.health_status["status"] = "degraded"
            else:
                self.health_status["status"] = "healthy"
                
            return self.health_status
        except Exception as e:
            logger.error(f"Error checking health for module {self.name}: {str(e)}")
            self.health_status["status"] = "error"
            self.health_status["last_check"] = datetime.datetime.now().isoformat()
            self.health_status["details"]["health_check_error"] = str(e)
            return self.health_status
    
    def check_dependencies(self) -> List[Dict[str, Any]]:
        """
        Check if all dependencies are available and healthy
        
        Returns:
            list: List of dependency statuses
        """
        results = []
        registry = self.get_registry()
        
        for dep in self.dependencies:
            module_name = dep["module_name"]
            required_services = dep["required_services"]
            is_critical = dep["is_critical"]
            
            dep_status = {
                "module_name": module_name,
                "is_critical": is_critical,
                "status": "healthy",
                "details": {}
            }
            
            # Check if all required services are available
            missing_services = []
            for service_name in required_services:
                service = registry.get_service(service_name)
                if service is None:
                    missing_services.append(service_name)
            
            if missing_services:
                if is_critical:
                    dep_status["status"] = "error"
                else:
                    dep_status["status"] = "degraded"
                    
                dep_status["details"]["missing_services"] = missing_services
                
            results.append(dep_status)
        
        return results
    
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
            "health": self.health_status["status"],
            "last_check": self.health_status["last_check"]
        }
