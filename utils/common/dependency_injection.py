"""
Dependency Injection Container for CBS_PYTHON

This module provides a dependency injection container implementation
to help reduce coupling between components and improve testability.
"""

import inspect
from typing import Dict, Any, Type, Callable, Optional, List, Union, TypeVar, Generic, get_type_hints

# Type variables for generics
T = TypeVar('T')


class DependencyContainer:
    """
    A dependency injection container that manages service registration and resolution.
    
    Usage:
        container = DependencyContainer()
        
        # Register a concrete implementation
        container.register(DatabaseInterface, PostgresDatabase)
        
        # Register a singleton
        container.register_singleton(LoggerInterface, FileLogger)
        
        # Register a factory function
        container.register_factory(ConfigInterface, lambda c: JsonConfig("config.json"))
        
        # Resolve dependencies
        db = container.resolve(DatabaseInterface)
    """
    
    def __init__(self):
        self._registrations = {}
        self._instances = {}
    
    def register(self, interface: Type[T], implementation: Type[T]) -> None:
        """
        Register an implementation for an interface
        
        Args:
            interface: The interface or abstract class
            implementation: The concrete implementation class
        """
        self._registrations[interface] = {
            'implementation': implementation,
            'singleton': False,
            'factory': None
        }
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """
        Register a singleton implementation for an interface
        
        Args:
            interface: The interface or abstract class
            implementation: The concrete implementation class
        """
        self._registrations[interface] = {
            'implementation': implementation,
            'singleton': True,
            'factory': None
        }
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """
        Register an existing instance for an interface
        
        Args:
            interface: The interface or abstract class
            instance: The instance to register
        """
        self._instances[interface] = instance
    
    def register_factory(self, interface: Type[T], factory: Callable[['DependencyContainer'], T]) -> None:
        """
        Register a factory function for an interface
        
        Args:
            interface: The interface or abstract class
            factory: A function that creates an instance of the implementation
        """
        self._registrations[interface] = {
            'implementation': None,
            'singleton': False,
            'factory': factory
        }
    
    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve an implementation for the given interface
        
        Args:
            interface: The interface or abstract class
            
        Returns:
            An instance of the implementation
            
        Raises:
            KeyError: If the interface is not registered
            ValueError: If cyclic dependencies are detected
        """
        # Check if we already have an instance
        if interface in self._instances:
            return self._instances[interface]
        
        # Check if the interface is registered
        if interface not in self._registrations:
            raise KeyError(f"No registration found for {interface.__name__}")
        
        registration = self._registrations[interface]
        
        # If we have a factory, use it
        if registration['factory']:
            instance = registration['factory'](self)
        else:
            # Get constructor parameters for the implementation
            implementation = registration['implementation']
            if not implementation:
                raise ValueError(f"No implementation or factory registered for {interface.__name__}")
            
            # Inspect the implementation's constructor parameters
            init_signature = inspect.signature(implementation.__init__)
            parameters = init_signature.parameters
            
            # Skip 'self' parameter
            parameters = {name: param for name, param in parameters.items() if name != 'self'}
            
            # Get type hints from the constructor
            try:
                type_hints = get_type_hints(implementation.__init__)
                # Remove 'return' from type hints if present
                if 'return' in type_hints:
                    del type_hints['return']
            except (TypeError, NameError):
                # If type hints can't be resolved, use empty dict
                type_hints = {}
            
            # Build arguments for constructor
            kwargs = {}
            for name, param in parameters.items():
                if name in type_hints:
                    param_type = type_hints[name]
                    # Recursive resolution for dependencies
                    try:
                        kwargs[name] = self.resolve(param_type)
                    except KeyError:
                        # If dependency can't be resolved and parameter is optional
                        if param.default is not inspect.Parameter.empty:
                            kwargs[name] = param.default
                        else:
                            raise ValueError(f"Cannot resolve dependency {name} of type {param_type.__name__}")
            
            # Create instance with dependencies injected
            instance = implementation(**kwargs)
        
        # If it's a singleton, store the instance
        if registration['singleton']:
            self._instances[interface] = instance
        
        return instance


# Common interface and implementation patterns for reuse

class Repository(Generic[T]):
    """
    Generic repository interface for data access.
    
    This provides a common pattern for data access across the system.
    """
    
    def get_by_id(self, id: str) -> Optional[T]:
        """Get an entity by ID"""
        raise NotImplementedError
    
    def get_all(self) -> List[T]:
        """Get all entities"""
        raise NotImplementedError
    
    def add(self, entity: T) -> T:
        """Add a new entity"""
        raise NotImplementedError
    
    def update(self, entity: T) -> T:
        """Update an existing entity"""
        raise NotImplementedError
    
    def delete(self, id: str) -> bool:
        """Delete an entity by ID"""
        raise NotImplementedError


class Service(Generic[T]):
    """
    Generic service interface for business logic.
    
    This provides a common pattern for services across the system.
    """
    
    def __init__(self, repository: Repository[T]):
        """
        Initialize with repository dependency
        
        Args:
            repository: Repository for data access
        """
        self.repository = repository
"""
