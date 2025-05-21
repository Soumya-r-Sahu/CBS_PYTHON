"""
Core Banking System - Module Interface Unit Tests

This module contains unit tests for the module interface functionality.
"""

import pytest
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import module interface
from utils.lib.module_interface import ModuleInterface, ModuleRegistry


class TestModuleRegistry(unittest.TestCase):
    """Unit tests for the ModuleRegistry class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a clean registry for each test
        ModuleRegistry._instance = None
        self.registry = ModuleRegistry.get_instance()
    
    def test_registry_singleton(self):
        """Test that ModuleRegistry is a singleton."""
        registry1 = ModuleRegistry.get_instance()
        registry2 = ModuleRegistry.get_instance()
        
        self.assertIs(registry1, registry2)
    
    def test_module_registration(self):
        """Test registering a module."""
        class TestModule(ModuleInterface):
            def register_services(self):
                return True
        
        module = TestModule("test_module", "1.0.0")
        result = self.registry.register_module(module)
        
        self.assertTrue(result)
        self.assertEqual(len(self.registry.modules), 1)
        self.assertIn("test_module", self.registry.modules)
    
    def test_get_module(self):
        """Test getting a module by name."""
        class TestModule(ModuleInterface):
            def register_services(self):
                return True
        
        module = TestModule("test_module", "1.0.0")
        self.registry.register_module(module)
        
        retrieved_module = self.registry.get_module("test_module")
        self.assertIs(retrieved_module, module)
        
        # Try to get a non-existent module
        non_existent = self.registry.get_module("non_existent")
        self.assertIsNone(non_existent)
    
    def test_list_modules(self):
        """Test listing all modules."""
        class TestModule1(ModuleInterface):
            def register_services(self):
                return True
        
        class TestModule2(ModuleInterface):
            def register_services(self):
                return True
        
        module1 = TestModule1("test_module1", "1.0.0")
        module2 = TestModule2("test_module2", "2.0.0")
        
        self.registry.register_module(module1)
        self.registry.register_module(module2)
        
        modules = self.registry.list_modules()
        
        self.assertEqual(len(modules), 2)
        self.assertEqual(modules[0]["name"], "test_module1")
        self.assertEqual(modules[1]["name"], "test_module2")


# You can run this test file directly
if __name__ == "__main__":
    unittest.main()
