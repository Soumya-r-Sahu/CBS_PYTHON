"""
Dependency Injection Container

This module provides dependency injection for the HR-ERP employee management module.
"""

from typing import Dict, Any, TypeVar, Type, Callable

from ..domain.repositories.employee_repository import EmployeeRepository
from ..application.use_cases.create_employee_use_case import CreateEmployeeUseCase
from .repositories.sql_employee_repository import SqlEmployeeRepository
from .database.database_connection import DatabaseConnection

T = TypeVar('T')

class EmployeeManagementDIContainer:
    """
    Dependency Injection Container for Employee Management module
    
    This class manages object instantiation and wiring of dependencies
    following the SOLID principles of Clean Architecture.
    """
    
    def __init__(self):
        """Initialize the DI container"""
        self._services: Dict[Type, Callable[[], Any]] = {}
        self._instances: Dict[Type, Any] = {}
        self._initialize_container()
    
    def _initialize_container(self) -> None:
        """
        Register services with the container
        
        This method configures all dependencies needed for the
        employee management module.
        """
        # Register database connection
        self.register(DatabaseConnection, lambda: DatabaseConnection())
        
        # Register repositories
        self.register(
            EmployeeRepository, 
            lambda: SqlEmployeeRepository(self.resolve(DatabaseConnection))
        )
        
        # Register use cases
        self.register(
            CreateEmployeeUseCase, 
            lambda: CreateEmployeeUseCase(self.resolve(EmployeeRepository))
        )
    
    def register(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """
        Register a service with the container
        
        Args:
            interface: The interface or type to register
            factory: Factory function to create the service
        """
        self._services[interface] = factory
    
    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a service from the container
        
        Args:
            interface: The interface or type to resolve
            
        Returns:
            Instance of the requested service
            
        Raises:
            KeyError: If the requested service is not registered
        """
        # Return cached instance if available
        if interface in self._instances:
            return self._instances[interface]
        
        # Create new instance
        if interface in self._services:
            instance = self._services[interface]()
            self._instances[interface] = instance
            return instance
        
        raise KeyError(f"Service not registered: {interface.__name__}")
    
    def clear(self) -> None:
        """Clear all cached instances"""
        self._instances.clear()


# Create a singleton instance
container = EmployeeManagementDIContainer()

def get_container() -> EmployeeManagementDIContainer:
    """
    Get the container instance
    
    Returns:
        The dependency injection container
    """
    return container
"""
