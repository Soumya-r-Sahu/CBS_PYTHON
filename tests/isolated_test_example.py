"""
Isolated test module for module health check demonstration.

This module doesn't depend on the existing code structure and demonstrates how the tests should work.
"""

import unittest


class ModuleInterface:
    """Simple module interface for demonstration purposes."""
    
    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.active = False
        self.health_status = {
            "status": "initializing",
            "last_check": None,
            "details": {}
        }
    
    def check_health(self):
        """Check module health"""
        health_details = {
            "module_name": self.name,
            "version": self.version,
            "status": "active" if self.active else "inactive",
            "checks": [],
            "overall_status": "healthy"
        }
        
        # Add a sample check
        health_details["checks"].append({
            "name": "sample_check",
            "status": "healthy",
            "message": "Sample check passed"
        })
        
        return health_details


class TestModuleHealthCheck(unittest.TestCase):
    """Demo test case for module health check."""
    
    def setUp(self):
        """Set up test environment."""
        self.module = ModuleInterface("test_module", "1.0.0")
    
    def test_module_health_format(self):
        """Test that module health reports follow the standardized format."""
        # Get health report
        health = self.module.check_health()
        
        # Verify format
        required_fields = ["module_name", "version", "status", "checks", "overall_status"]
        for field in required_fields:
            self.assertIn(field, health)
        
        # Verify specific field values
        self.assertEqual(health["module_name"], "test_module")
        self.assertEqual(health["version"], "1.0.0")
        
        # Verify checks format
        self.assertIsInstance(health["checks"], list)
        self.assertEqual(len(health["checks"]), 1)
        
        # Verify check content
        check = health["checks"][0]
        self.assertEqual(check["name"], "sample_check")
        self.assertEqual(check["status"], "healthy")
        self.assertEqual(check["message"], "Sample check passed")


if __name__ == "__main__":
    unittest.main()
