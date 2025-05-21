"""
Singleton Pattern Implementation

This module provides a concrete implementation of the Singleton design pattern.
"""

from utils.design_patterns import Singleton, singleton

# Example 1: Using metaclass
class SingletonClass(metaclass=Singleton):
    """
    Example singleton class using metaclass.
    """
    def __init__(self):
        self.value = None
    
    def set_value(self, value):
        self.value = value
    
    def get_value(self):
        return self.value

# Example 2: Using decorator
@singleton
class SingletonDecorated:
    """
    Example singleton class using decorator.
    """
    def __init__(self):
        self.value = None
    
    def set_value(self, value):
        self.value = value
    
    def get_value(self):
        return self.value

def get_singleton_instance():
    """
    Get a singleton instance.
    """
    return SingletonClass()
