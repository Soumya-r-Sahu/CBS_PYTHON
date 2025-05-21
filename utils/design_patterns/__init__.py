"""
Singleton Design Pattern

This module provides implementation of the Singleton design pattern.
"""

class Singleton:
    """
    A non-thread-safe helper class to implement the Singleton pattern.
    
    This class is used as a metaclass to create singleton classes.
    
    Usage:
        class Logger(metaclass=Singleton):
            def __init__(self):
                self.logs = []
                
            def log(self, message):
                self.logs.append(message)
                
        # All instances will be the same
        logger1 = Logger()
        logger2 = Logger()
        assert logger1 is logger2
    """
    
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def singleton(cls):
    """
    A decorator to implement the Singleton pattern.
    
    Usage:
        @singleton
        class Logger:
            def __init__(self):
                self.logs = []
                
            def log(self, message):
                self.logs.append(message)
                
        # All instances will be the same
        logger1 = Logger()
        logger2 = Logger()
        assert logger1 is logger2
    """
    instances = {}
    
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance
