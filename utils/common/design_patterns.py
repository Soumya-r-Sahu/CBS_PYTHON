"""
Design Patterns Module for CBS_PYTHON

This module provides implementations of common design patterns for use throughout the system.
It helps reduce code duplication and encourages consistent application architecture.
"""

import threading
import time
import logging
import functools
import inspect
from typing import Dict, Any, Type, Callable, Optional, List, Union, TypeVar, Generic

# Type variables for generics
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

# Configure logger
logger = logging.getLogger(__name__)

#-----------------------------------------
# Creational Patterns
#-----------------------------------------

class Singleton(type):
    """
    Singleton metaclass implementation.
    
    Usage:
        class Logger(metaclass=Singleton):
            def __init__(self):
                self.logs = []
    """
    _instances = {}
    _lock = threading.RLock()
    
    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


def singleton(cls):
    """
    Singleton decorator implementation.
    
    Usage:
        @singleton
        class Logger:
            def __init__(self):
                self.logs = []
    """
    instances = {}
    lock = threading.RLock()
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        with lock:
            if cls not in instances:
                instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


class Factory:
    """
    Generic Factory implementation.
    
    Usage:
        payment_factory = Factory()
        payment_factory.register("credit_card", CreditCardPayment)
        payment_factory.register("upi", UpiPayment)
        payment = payment_factory.create("credit_card", amount=100)
    """
    
    def __init__(self):
        self._creators = {}
    
    def register(self, key: str, creator: Type) -> None:
        """
        Register a class with the factory
        
        Args:
            key: Identifier for the class
            creator: Class to instantiate
        """
        self._creators[key] = creator
    
    def create(self, key: str, *args, **kwargs) -> Any:
        """
        Create an instance of the registered class
        
        Args:
            key: Identifier for the class
            *args: Positional arguments to pass to the constructor
            **kwargs: Keyword arguments to pass to the constructor
            
        Returns:
            Instance of the registered class
            
        Raises:
            ValueError: If key is not registered with the factory
        """
        creator = self._creators.get(key)
        if not creator:
            raise ValueError(f"Unknown key: {key}")
        return creator(*args, **kwargs)


class Builder(Generic[T]):
    """
    Generic Builder interface.
    
    Usage:
        class CarBuilder(Builder[Car]):
            def __init__(self):
                self.car = Car()
                
            def add_engine(self, engine: str) -> 'CarBuilder':
                self.car.engine = engine
                return self
                
            def add_wheels(self, count: int) -> 'CarBuilder':
                self.car.wheels = count
                return self
                
            def build(self) -> Car:
                return self.car
    """
    
    def build(self) -> T:
        """Build and return the object"""
        raise NotImplementedError("Builders must implement build()")


class Director:
    """
    Director for the Builder pattern.
    
    Usage:
        director = Director()
        car_builder = CarBuilder()
        sports_car = director.build(car_builder, lambda b: b.add_engine("V8").add_wheels(4))
    """
    
    def build(self, builder: Builder[T], configure: Callable[[Builder[T]], Builder[T]]) -> T:
        """
        Build an object using the given builder and configuration function
        
        Args:
            builder: Builder instance
            configure: Function to configure the builder
            
        Returns:
            Built object
        """
        return configure(builder).build()


#-----------------------------------------
# Structural Patterns
#-----------------------------------------

class Adapter:
    """
    Generic Adapter implementation.
    
    Usage:
        class LegacySystem:
            def old_method(self, value):
                return f"Legacy: {value}"
                
        class NewSystem:
            def new_method(self, data):
                return f"New: {data}"
                
        class SystemAdapter(Adapter):
            def __init__(self, adaptee):
                self.adaptee = adaptee
                
            def new_method(self, data):
                return self.adaptee.old_method(data)
    """
    
    def __init__(self, adaptee: Any):
        """
        Initialize with the object to adapt
        
        Args:
            adaptee: Object being adapted
        """
        self.adaptee = adaptee


class Proxy:
    """
    Generic Proxy implementation.
    
    Usage:
        class ExpensiveObject:
            def process(self, data):
                # Expensive operation
                return data
                
        class ExpensiveObjectProxy(Proxy):
            def __init__(self):
                self._real_object = None
                
            def process(self, data):
                if self._real_object is None:
                    self._real_object = ExpensiveObject()
                return self._real_object.process(data)
    """
    
    def __init__(self, real_subject: Optional[Any] = None):
        """
        Initialize with the real subject (optional)
        
        Args:
            real_subject: The real object being proxied
        """
        self._real_subject = real_subject


class Composite:
    """
    Base class for the Composite pattern.
    
    Usage:
        class FileSystemItem(Composite):
            def __init__(self, name):
                super().__init__()
                self.name = name
                
            def display(self):
                pass
                
        class File(FileSystemItem):
            def display(self):
                return f"File: {self.name}"
                
        class Directory(FileSystemItem):
            def display(self):
                result = [f"Directory: {self.name}"]
                for child in self.children:
                    result.append(f"  {child.display()}")
                return "\\n".join(result)
    """
    
    def __init__(self):
        """Initialize with empty children list"""
        self.children = []
    
    def add(self, component: 'Composite') -> None:
        """
        Add a child component
        
        Args:
            component: Child component to add
        """
        self.children.append(component)
    
    def remove(self, component: 'Composite') -> None:
        """
        Remove a child component
        
        Args:
            component: Child component to remove
        """
        self.children.remove(component)


#-----------------------------------------
# Behavioral Patterns
#-----------------------------------------

class Observer:
    """
    Observer interface.
    
    Usage:
        class ConcreteObserver(Observer):
            def update(self, subject, *args, **kwargs):
                print(f"Received update from {subject} with {args} and {kwargs}")
    """
    
    def update(self, subject: Any, *args, **kwargs) -> None:
        """
        Receive update from subject
        
        Args:
            subject: Subject that triggered the update
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        raise NotImplementedError("Observers must implement update()")


class Observable:
    """
    Subject in the Observer pattern.
    
    Usage:
        class ConcreteObservable(Observable):
            def __init__(self):
                super().__init__()
                self._state = None
                
            @property
            def state(self):
                return self._state
                
            @state.setter
            def state(self, value):
                self._state = value
                self.notify_observers("state_changed", new_state=value)
    """
    
    def __init__(self):
        """Initialize with empty observers list"""
        self._observers = []
    
    def add_observer(self, observer: Observer) -> None:
        """
        Add an observer
        
        Args:
            observer: Observer to add
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: Observer) -> None:
        """
        Remove an observer
        
        Args:
            observer: Observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, *args, **kwargs) -> None:
        """
        Notify all observers
        
        Args:
            *args: Additional arguments to pass to observers
            **kwargs: Additional keyword arguments to pass to observers
        """
        for observer in self._observers:
            observer.update(self, *args, **kwargs)


class Strategy:
    """
    Strategy interface.
    
    Usage:
        class ConcreteStrategy(Strategy):
            def execute(self, data):
                return f"Processed {data}"
    """
    
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the strategy
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result of strategy execution
        """
        raise NotImplementedError("Strategies must implement execute()")


class StrategyContext:
    """
    Context for the Strategy pattern.
    
    Usage:
        add_strategy = ConcreteStrategy()
        context = StrategyContext(add_strategy)
        result = context.execute_strategy(a=1, b=2)
    """
    
    def __init__(self, strategy: Strategy = None):
        """
        Initialize with a strategy (optional)
        
        Args:
            strategy: Initial strategy
        """
        self._strategy = strategy
    
    @property
    def strategy(self) -> Optional[Strategy]:
        """Get the current strategy"""
        return self._strategy
    
    @strategy.setter
    def strategy(self, strategy: Strategy) -> None:
        """
        Set the strategy
        
        Args:
            strategy: New strategy
        """
        self._strategy = strategy
    
    def execute_strategy(self, *args, **kwargs) -> Any:
        """
        Execute the current strategy
        
        Args:
            *args: Positional arguments to pass to strategy
            **kwargs: Keyword arguments to pass to strategy
            
        Returns:
            Result of strategy execution
            
        Raises:
            ValueError: If no strategy is set
        """
        if not self._strategy:
            raise ValueError("No strategy set")
        return self._strategy.execute(*args, **kwargs)


class Command:
    """
    Command interface.
    
    Usage:
        class PrintCommand(Command):
            def __init__(self, message):
                self.message = message
                
            def execute(self):
                print(self.message)
                
            def undo(self):
                print(f"Undo print: {self.message}")
    """
    
    def execute(self) -> None:
        """Execute the command"""
        raise NotImplementedError("Commands must implement execute()")
    
    def undo(self) -> None:
        """Undo the command (optional)"""
        pass


class CommandInvoker:
    """
    Invoker for the Command pattern with history for undo.
    
    Usage:
        invoker = CommandInvoker()
        invoker.execute_command(PrintCommand("Hello"))
        invoker.execute_command(PrintCommand("World"))
        invoker.undo_last()  # Undoes "World"
    """
    
    def __init__(self):
        """Initialize with empty history"""
        self._history = []
    
    def execute_command(self, command: Command) -> None:
        """
        Execute a command and add to history
        
        Args:
            command: Command to execute
        """
        command.execute()
        self._history.append(command)
    
    def undo_last(self) -> bool:
        """
        Undo the last command
        
        Returns:
            True if a command was undone, False if history was empty
        """
        if not self._history:
            return False
        
        command = self._history.pop()
        command.undo()
        return True
    
    def undo_all(self) -> int:
        """
        Undo all commands in history
        
        Returns:
            Number of commands undone
        """
        count = 0
        while self.undo_last():
            count += 1
        return count


class ChainHandler:
    """
    Handler in the Chain of Responsibility pattern.
    
    Usage:
        class ConcreteHandler1(ChainHandler):
            def handle(self, request):
                if request == "type1":
                    return "Handled by Handler1"
                return self._next_handler.handle(request) if self._next_handler else None
                
        handler1 = ConcreteHandler1()
        handler2 = ConcreteHandler2()
        handler1.set_next(handler2)
        result = handler1.handle("type2")  # Will be handled by Handler2
    """
    
    def __init__(self):
        """Initialize with no next handler"""
        self._next_handler = None
    
    def set_next(self, handler: 'ChainHandler') -> 'ChainHandler':
        """
        Set the next handler in the chain
        
        Args:
            handler: Next handler
            
        Returns:
            The next handler (for chaining)
        """
        self._next_handler = handler
        return handler
    
    def handle(self, request: Any) -> Optional[Any]:
        """
        Handle the request or pass to the next handler
        
        Args:
            request: Request to handle
            
        Returns:
            Result of handling the request, or None if not handled
        """
        raise NotImplementedError("Handlers must implement handle()")


#-----------------------------------------
# Function Decorators
#-----------------------------------------

def memoize(func: Callable) -> Callable:
    """
    Decorator for memoizing function results.
    
    Usage:
        @memoize
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
    """
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create a key from the arguments
        key = str(args) + str(sorted(kwargs.items()))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    
    return wrapper


def retry(attempts: int = 3, delay: float = 1.0, exceptions: List[Type[Exception]] = None):
    """
    Decorator for retrying functions on exception.
    
    Usage:
        @retry(attempts=3, delay=2.0, exceptions=[ConnectionError])
        def connect_to_database():
            # Connection logic that might fail
            pass
    """
    exceptions = exceptions or [Exception]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_exception = e
                    if attempt < attempts - 1:  # Don't sleep on the last attempt
                        time.sleep(delay)
            
            if last_exception:
                raise last_exception
        
        return wrapper
    
    return decorator


def method_timer(func: Callable) -> Callable:
    """
    Decorator for timing method execution.
    
    Usage:
        @method_timer
        def slow_function():
            time.sleep(1.5)
            return "Done"
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"Method {func.__name__} executed in {execution_time:.4f} seconds")
        return result
    
    return wrapper


def deprecated(message: Optional[str] = None):
    """
    Decorator for marking methods as deprecated.
    
    Usage:
        @deprecated("Use new_method() instead")
        def old_method():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warning = f"Call to deprecated function {func.__name__}"
            if message:
                warning += f": {message}"
            logger.warning(warning)
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
