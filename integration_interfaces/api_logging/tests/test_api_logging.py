"""
API Logging Tests - Core Banking System

This module contains unit tests for API logging functionality.
"""
import unittest
import os
import tempfile
import shutil
from datetime import datetime
import json

from ..models.log_models import ApiLogEntry
from ..services.log_service import ApiLoggerService
from ..utils.log_utils import group_errors_by_type



# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
class TestApiLogging(unittest.TestCase):
    """Test case for API logging functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary log directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test logger service instance
        self.logger_service = ApiLoggerService()
        self.logger_service.log_dir = self.temp_dir
        self.logger_service.max_file_size_mb = 1
        self.logger_service.sensitive_fields = ["password", "token", "secret"]
        
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
        
    def test_log_api_call(self):
        """Test logging an API call"""
        # Test data
        endpoint = "/api/test"
        request_data = {
            "user_id": "12345",
            "password": "secret123",
            "action": "test"
        }
        response_data = {
            "status": "success",
            "message": "Test completed",
            "token": "abc123xyz"
        }
        status = "success"
        
        # Log the API call
        self.logger_service.log_api_call(endpoint, request_data, response_data, status)
        
        # Check if log file was created
        log_files = os.listdir(self.temp_dir)
        self.assertTrue(len(log_files) > 0, "No log file was created")
        
        # Check log content
        log_file = os.path.join(self.temp_dir, log_files[0])
        with open(log_file, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content)
            
            # Check basic fields
            self.assertEqual(log_entry["endpoint"], endpoint)
            self.assertEqual(log_entry["status"], status)
            
            # Check that sensitive data was sanitized
            self.assertEqual(log_entry["request"]["password"], "***REDACTED***")
            self.assertEqual(log_entry["response"]["token"], "***REDACTED***")
            
            # Check that non-sensitive data was preserved
            self.assertEqual(log_entry["request"]["user_id"], "12345")
            self.assertEqual(log_entry["response"]["message"], "Test completed")
            
    def test_group_errors(self):
        """Test grouping errors by type"""
        # Create test logs
        logs = [
            ApiLogEntry(
                timestamp=datetime.utcnow().isoformat(),
                endpoint="/api/test1",
                request={},
                response={},
                status="error",
                error="ValidationError: Invalid parameter"
            ),
            ApiLogEntry(
                timestamp=datetime.utcnow().isoformat(),
                endpoint="/api/test2",
                request={},
                response={},
                status="error",
                error="ValidationError: Missing required field"
            ),
            ApiLogEntry(
                timestamp=datetime.utcnow().isoformat(),
                endpoint="/api/test3",
                request={},
                response={},
                status="error",
                error="DatabaseError: Connection failed"
            ),
            ApiLogEntry(
                timestamp=datetime.utcnow().isoformat(),
                endpoint="/api/test1",
                request={},
                response={},
                status="success",
                error=None
            )
        ]
        
        # Group the errors
        error_groups = group_errors_by_type(logs)
        
        # Check results
        self.assertEqual(len(error_groups), 2, "Should have 2 error groups")
        
        # ValidationError group should have count of 2
        validation_group = next((g for g in error_groups if g.error_type == "ValidationError"), None)
        self.assertIsNotNone(validation_group, "ValidationError group not found")
        self.assertEqual(validation_group.count, 2, "ValidationError count should be 2")
        
        # DatabaseError group should have count of 1
        db_group = next((g for g in error_groups if g.error_type == "DatabaseError"), None)
        self.assertIsNotNone(db_group, "DatabaseError group not found")
        self.assertEqual(db_group.count, 1, "DatabaseError count should be 1")


if __name__ == '__main__':
    unittest.main()
