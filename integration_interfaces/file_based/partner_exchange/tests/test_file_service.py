"""
Partner File Exchange Tests - Core Banking System

This module contains unit tests for partner file exchange functionality.
"""
import unittest
import os
import tempfile
import shutil
from datetime import datetime

# Import the modules we want to test
from ..config.file_config import PartnerFileConfig
from ..models.file_models import PartnerFileEntry
from ..services.file_service import PartnerFileService
from ..controllers.file_controller import PartnerFileController



# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
class TestPartnerFileExchange(unittest.TestCase):
    """Test cases for partner file exchange functionality"""
    
    def setUp(self):
        """Set up the test environment"""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.incoming_dir = os.path.join(self.temp_dir, "incoming")
        self.outgoing_dir = os.path.join(self.temp_dir, "outgoing")
        self.archive_dir = os.path.join(self.temp_dir, "archive")
        self.error_dir = os.path.join(self.temp_dir, "error")
        
        # Create the directories
        os.makedirs(self.incoming_dir, exist_ok=True)
        os.makedirs(self.outgoing_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs(self.error_dir, exist_ok=True)
        
        # Create a test file service with our temp directories
        self.file_service = PartnerFileService()
        self.file_service.incoming_dir = self.incoming_dir
        self.file_service.outgoing_dir = self.outgoing_dir
        self.file_service.archive_dir = self.archive_dir
        self.file_service.error_dir = self.error_dir
        
        # Create sample data
        self.sample_entries = [
            PartnerFileEntry(
                transaction_id="TX123456",
                partner_id="PARTNERBANK",
                amount=1000.00,
                status="SUCCESS",
                timestamp="2025-05-13T10:00:00Z"
            ),
            PartnerFileEntry(
                transaction_id="TX789012",
                partner_id="PARTNERBANK",
                amount=2500.50,
                status="SUCCESS",
                timestamp="2025-05-13T11:30:00Z"
            )
        ]
    
    def tearDown(self):
        """Clean up the test environment"""
        # Remove the temporary directory and all its contents
        shutil.rmtree(self.temp_dir)
    
    def test_create_csv_file(self):
        """Test creating a CSV partner file"""
        # Create a test file
        filename = self.file_service.create_partner_file(
            "PARTNERBANK", 
            self.sample_entries, 
            "test", 
            "csv"
        )
        
        # Check the file exists
        file_path = os.path.join(self.outgoing_dir, filename)
        self.assertTrue(os.path.exists(file_path))
        
        # Check the file content
        with open(file_path, 'r') as f:
            content = f.read()
            self.assertIn("TX123456", content)
            self.assertIn("PARTNERBANK", content)
            self.assertIn("1000.0", content)
    
    def test_create_json_file(self):
        """Test creating a JSON partner file"""
        # Create a test file
        filename = self.file_service.create_partner_file(
            "PARTNERBANK", 
            self.sample_entries, 
            "test", 
            "json"
        )
        
        # Check the file exists
        file_path = os.path.join(self.outgoing_dir, filename)
        self.assertTrue(os.path.exists(file_path))
        
        # Check the file content
        with open(file_path, 'r') as f:
            content = f.read()
            self.assertIn("TX123456", content)
            self.assertIn("PARTNERBANK", content)
            self.assertIn("1000.0", content)
            self.assertIn("partner_file_format_version", content)


if __name__ == '__main__':
    unittest.main()
