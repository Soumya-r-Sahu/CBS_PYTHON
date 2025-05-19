"""
Singleton decorator for implementing the singleton pattern.

This module provides a decorator that can be applied to any class to make it
follow the singleton pattern, ensuring that only one instance of the class
is created throughout the application lifecycle.

Example:
    from utils.design_patterns import singleton
    
    @singleton
    class ConfigManager:
        def __init__(self):
            self.config = {}
            # Initialization code
            
        def get_config(self, key):
            return self.config.get(key)
"""

def singleton(cls):
    """
    Decorator that transforms a class into a singleton.
    
    This decorator ensures that only one instance of the class is created,
    and returns that same instance for all subsequent calls to the class constructor.
    
    Args:
        cls: The class to transform into a singleton.
        
    Returns:
        The singleton wrapper around the class.
    """
    instances = {}
    
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance
