"""
Core Banking System - Module Health Check Integration Tests

This module contains integration tests for the module health check system.
It verifies that health checks work correctly across modules.
"""

import pytest
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import module interfaces and registry
from utils.lib.module_interface import ModuleInterface, ModuleRegistry


class TestHealthCheckSystem(unittest.TestCase):
    """Integration tests for the module health check system."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a clean registry for each test
        ModuleRegistry._instance = None
        self.registry = ModuleRegistry.get_instance()
        
        # Mock module for testing
        class TestHealthModule(ModuleInterface):
            def __init__(self, name, version, db_status="healthy", service_status="healthy"):
                super().__init__(name, version)
                self._db_status = db_status
                self._service_status = service_status
            
            def register_services(self):
                return True
            
            def _check_database_connections(self):
                return {
                    "status": self._db_status,
                    "message": f"Database status: {self._db_status}"
                }
            
            def _check_service_registrations(self):
                return {
                    "status": self._service_status,
                    "message": f"Service status: {self._service_status}"
                }
        
        # Create test modules with different health statuses
        self.healthy_module = TestHealthModule("healthy_module", "1.0.0")
        self.degraded_db_module = TestHealthModule("degraded_db_module", "1.0.0", db_status="degraded")
        self.critical_service_module = TestHealthModule("critical_service_module", "1.0.0", service_status="critical")
        
        # Register modules
        self.registry.register_module(self.healthy_module)
        self.registry.register_module(self.degraded_db_module)
        self.registry.register_module(self.critical_service_module)
    
    def test_module_health_report_format(self):
        """Test that module health reports follow the standardized format."""
        # Activate the module
        self.healthy_module.activate()
        
        # Get health report
        health = self.healthy_module.check_health()
        
        # Verify format
        required_fields = [
            "module_name", "version", "timestamp", "status",
            "checks", "dependencies_status", "services_status",
            "database_status", "overall_status"
        ]
        
        for field in required_fields:
            self.assertIn(field, health)
        
        # Verify checks format
        self.assertIsInstance(health["checks"], list)
        if health["checks"]:
            check = health["checks"][0]
            self.assertIn("name", check)
            self.assertIn("status", check)
            self.assertIn("message", check)
    
    def test_registry_health_check_all(self):
        """Test the registry-level health check for all modules."""
        # Activate all modules
        self.registry.activate_all()
        
        # Check health of all modules
        health_report = self.registry.check_health_all()
        
        # Verify the report contains all modules
        self.assertEqual(len(health_report), 3)
        self.assertIn("healthy_module", health_report)
        self.assertIn("degraded_db_module", health_report)
        self.assertIn("critical_service_module", health_report)
        
        # Verify healthy module status
        self.assertEqual(health_report["healthy_module"]["overall_status"], "healthy")
        
        # Verify degraded module status
        self.assertEqual(health_report["degraded_db_module"]["database_status"], "degraded")
        self.assertEqual(health_report["degraded_db_module"]["overall_status"], "degraded")
        
        # Verify critical module status
        self.assertEqual(health_report["critical_service_module"]["services_status"], "critical")
        self.assertEqual(health_report["critical_service_module"]["overall_status"], "critical")
    
    def test_health_check_propagation(self):
        """Test that health check issues properly propagate to dependent modules."""
        # Create a module with dependencies
        class DependentModule(ModuleInterface):
            def register_services(self):
                return True
        
        dependent_module = DependentModule("dependent_module", "1.0.0")
        dependent_module.register_dependency("critical_service_module", ["service.test"], is_critical=True)
        
        # Register and activate
        self.registry.register_module(dependent_module)
        self.registry.activate_all()
        
        # Check health
        dependent_health = dependent_module.check_health()
        
        # The dependent module should report critical status due to dependency
        self.assertEqual(dependent_health["dependencies_status"], "critical")
        self.assertEqual(dependent_health["overall_status"], "critical")


if __name__ == "__main__":
    unittest.main()
