"""
Design Patterns Module

This module implements common design patterns for use throughout the system.
"""
from functools import wraps
from typing import Dict, Any, Type, Callable, Optional, List, Union
import threading
import time
import logging

# Set up logger
logger = logging.getLogger(__name__)

class Singleton:
    """
    A metaclass that creates a Singleton of any class that specifies it as its metaclass.
    
    Usage:
        class MyClass(metaclass=Singleton):
            pass
    """
    _instances = {}
    _lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                # Check again in case another thread acquired the lock first
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def singleton(cls):
    """
    A decorator that makes a class a Singleton.
    
    Usage:
        @singleton
        class MyClass:
            pass
    """
    instances = {}
    lock = threading.Lock()
    
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


class Observable:
    """
    Implements the Observer pattern (Subject/Observable).
    
    This class allows objects to register as observers and be notified
    when the state of the observable changes.
    """
    
    def __init__(self):
        self._observers = []
    
    def register_observer(self, observer):
        """Register an observer to be notified of changes."""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer):
        """Remove an observer from the notification list."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, *args, **kwargs):
        """Notify all registered observers."""
        for observer in self._observers:
            observer.update(self, *args, **kwargs)


class Factory:
    """
    Implements the Factory pattern.
    
    This class allows registering and creating objects of various types.
    """
    
    def __init__(self):
        self._creators = {}
    
    def register(self, object_type, creator):
        """Register a creator function for a given object type."""
        self._creators[object_type] = creator
    
    def create(self, object_type, *args, **kwargs):
        """Create an object of the given type."""
        creator = self._creators.get(object_type)
        if not creator:
            raise ValueError(f"Unknown object type: {object_type}")
        return creator(*args, **kwargs)


class Strategy:
    """
    Base class for implementing the Strategy pattern.
    
    This allows the algorithm to be selected at runtime.
    """
    
    def execute(self, *args, **kwargs):
        """Execute the strategy."""
        raise NotImplementedError("Strategy.execute must be implemented by subclasses")


class StrategyContext:
    """
    Context for the Strategy pattern.
    
    This class maintains a reference to a Strategy object and delegates
    execution to it.
    """
    
    def __init__(self, strategy=None):
        self._strategy = strategy
    
    def set_strategy(self, strategy):
        """Change the strategy at runtime."""
        self._strategy = strategy
    
    def execute_strategy(self, *args, **kwargs):
        """Execute the current strategy."""
        if not self._strategy:
            raise ValueError("No strategy set")
        return self._strategy.execute(*args, **kwargs)


class Adapter:
    """
    Base class for implementing the Adapter pattern.
    
    This pattern allows objects with incompatible interfaces to work together.
    """
    
    def __init__(self, adaptee):
        self._adaptee = adaptee
    
    def interface(self, *args, **kwargs):
        """Implement the target interface."""
        raise NotImplementedError("Adapter.interface must be implemented by subclasses")


class Command:
    """
    Base class for implementing the Command pattern.
    
    This pattern encapsulates a request as an object.
    """
    
    def execute(self):
        """Execute the command."""
        raise NotImplementedError("Command.execute must be implemented by subclasses")
    
    def undo(self):
        """Undo the command."""
        raise NotImplementedError("Command.undo must be implemented by subclasses")


class CommandInvoker:
    """
    Invoker for the Command pattern.
    
    This class asks the command to carry out the request.
    """
    
    def __init__(self):
        self._commands = []
        self._current = -1
    
    def execute(self, command):
        """Execute a command and store it for potential undo."""
        command.execute()
        
        # Clear any undone commands
        if self._current < len(self._commands) - 1:
            self._commands = self._commands[:self._current+1]
        
        self._commands.append(command)
        self._current = len(self._commands) - 1
    
    def undo(self):
        """Undo the last executed command."""
        if self._current >= 0:
            command = self._commands[self._current]
            command.undo()
            self._current -= 1
            return True
        return False
    
    def redo(self):
        """Redo the last undone command."""
        if self._current < len(self._commands) - 1:
            self._current += 1
            command = self._commands[self._current]
            command.execute()
            return True
        return False


def memoize(func):
    """
    Decorator implementing the Memoization pattern.
    
    This caches the results of function calls to avoid redundant computation.
    """
    cache = {}
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create a key from the arguments
        # We convert args to a tuple to make it hashable
        key = str(args) + str(sorted(kwargs.items()))
        
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        
        return cache[key]
    
    # Add a method to clear the cache
    wrapper.clear_cache = lambda: cache.clear()
    
    return wrapper


class Proxy:
    """
    Base class for implementing the Proxy pattern.
    
    This pattern provides a surrogate or placeholder for another object.
    """
    
    def __init__(self, subject):
        self._subject = subject
    
    def request(self, *args, **kwargs):
        """Forward the request to the subject."""
        # Can perform additional logic before/after forwarding
        return self._subject.request(*args, **kwargs)


class Builder:
    """
    Base class for implementing the Builder pattern.
    
    This pattern separates the construction of a complex object from its representation.
    """
    
    def build_part_a(self):
        """Build part A of the product."""
        raise NotImplementedError("Builder.build_part_a must be implemented by subclasses")
    
    def build_part_b(self):
        """Build part B of the product."""
        raise NotImplementedError("Builder.build_part_b must be implemented by subclasses")
    
    def build_part_c(self):
        """Build part C of the product."""
        raise NotImplementedError("Builder.build_part_c must be implemented by subclasses")
    
    def get_result(self):
        """Get the constructed product."""
        raise NotImplementedError("Builder.get_result must be implemented by subclasses")


class Director:
    """
    Director for the Builder pattern.
    
    This class constructs an object using the Builder's interface.
    """
    
    def __init__(self, builder):
        self._builder = builder
    
    def construct(self):
        """Construct the product using the builder."""
        self._builder.build_part_a()
        self._builder.build_part_b()
        self._builder.build_part_c()
        return self._builder.get_result()


class Composite:
    """
    Base class for implementing the Composite pattern.
    
    This pattern lets clients treat individual objects and compositions uniformly.
    """
    
    def operation(self):
        """Perform the operation."""
        raise NotImplementedError("Composite.operation must be implemented by subclasses")
    
    def add(self, component):
        """Add a component to the composite."""
        raise NotImplementedError("Composite.add must be implemented by subclasses")
    
    def remove(self, component):
        """Remove a component from the composite."""
        raise NotImplementedError("Composite.remove must be implemented by subclasses")
    
    def get_child(self, index):
        """Get a child component."""
        raise NotImplementedError("Composite.get_child must be implemented by subclasses")
