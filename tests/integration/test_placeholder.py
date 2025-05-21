"""
Core Banking System - Module Health Check Integration Tests

This module contains integration tests for the module health check system.
It verifies that health checks work correctly across module boundaries.
"""

import pytest
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import module interfaces and registry
from utils.lib.module_interface import ModuleInterface, ModuleRegistry
from utils.lib.service_registry import ServiceRegistry


class TestModuleHealthChecks(unittest.TestCase):
    """Integration tests for the module health check system."""
    
    def setUp(self):
        """Set up test environment."""
        # Create clean registries for each test
        ModuleRegistry._instance = None
        self.module_registry = ModuleRegistry.get_instance()
        
        ServiceRegistry._instance = None
        self.service_registry = ServiceRegistry.get_instance()
        
        # Create test modules
        self.setup_test_modules()
    
    def setup_test_modules(self):
        """Set up test modules for the integration tests."""
        # Create a test module with dependencies
        class TestModule1(ModuleInterface):
            def register_services(self):
                registry = self.get_registry()
                registry.register("test_module1.service1", lambda: "Service 1", 
                                 version="1.0.0", module_name=self.name)
                registry.register("test_module1.service2", lambda: "Service 2", 
                                 version="1.0.0", module_name=self.name)
                self.service_registrations = ["test_module1.service1", "test_module1.service2"]
                return True
        
        # Create a dependent module
        class TestModule2(ModuleInterface):
            def register_services(self):
                registry = self.get_registry()
                registry.register("test_module2.service1", lambda: "Service 1", 
                                 version="1.0.0", module_name=self.name)
                self.service_registrations = ["test_module2.service1"]
                return True
        
        # Create and register the modules
        self.module1 = TestModule1("test_module1", "1.0.0")
        self.module2 = TestModule2("test_module2", "1.0.0")
        
        # Register dependencies
        self.module2.register_dependency("test_module1", ["test_module1.service1"], is_critical=True)
        
        # Register modules
        self.module_registry.register_module(self.module1)
        self.module_registry.register_module(self.module2)
    
    def test_health_check_dependencies(self):
        """Test that health checks correctly identify dependencies."""
        # Activate the first module
        self.module1.activate()
        
        # Check health of the second module
        health = self.module2.check_health()
        
        # Module2 should be healthy because its dependency (module1) is active
        self.assertIn("dependencies_status", health)
        self.assertEqual(health["dependencies_status"], "healthy")
        
        # Deactivate the first module
        self.module1.deactivate()
        
        # Re-check health of the second module
        health = self.module2.check_health()
        
        # Now module2 should report critical dependency issues
        self.assertEqual(health["dependencies_status"], "critical")
    
    def test_health_check_database(self):
        """Test that health checks correctly report database status."""
        # This is a mock test since we don't have a real database in unit tests
        # Activate the module
        self.module1.activate()
        
        # Check health
        health = self.module1.check_health()
        
        # Verify that database status is reported
        self.assertIn("database_status", health)
    
    def test_health_check_services(self):
        """Test that health checks correctly report service registration status."""
        # Activate the first module
        self.module1.activate()
        
        # Check health
        health = self.module1.check_health()
        
        # Verify that services are reported as healthy
        self.assertIn("services_status", health)
        self.assertEqual(health["services_status"], "healthy")
        
        # Manually remove a service from the registry
        registry = self.service_registry
        registry.services.pop("test_module1.service1", None)
        
        # Re-check health
        health = self.module1.check_health()
        
        # Services should now be degraded
        self.assertEqual(health["services_status"], "degraded")


# You can run this test file directly
if __name__ == "__main__":
    unittest.main()
