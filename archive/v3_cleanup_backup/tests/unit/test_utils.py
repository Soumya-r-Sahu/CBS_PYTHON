"""
Core Banking Utility Functions Unit Tests

This module contains unit tests for utility functions used in the Core Banking System.
"""

import pytest
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import utilities
from utils.id_utils import generate_id
from utils.encryption import encrypt_data, decrypt_data
from utils.validators import validate_email, validate_phone, validate_date
from utils.date_format import format_date, parse_date


class TestIdUtils(unittest.TestCase):
    """Unit tests for ID utility functions."""
    
    def test_generate_id(self):
        """Test generating IDs."""
        # Generate customer ID
        customer_id = generate_id("CUS")
        
        self.assertIsNotNone(customer_id)
        self.assertTrue(customer_id.startswith("CUS"))
        self.assertEqual(len(customer_id), 10)  # "CUS" + 7 chars
        
        # Generate account ID
        account_id = generate_id("ACC")
        
        self.assertIsNotNone(account_id)
        self.assertTrue(account_id.startswith("ACC"))
        self.assertEqual(len(account_id), 10)  # "ACC" + 7 chars
        
        # Generate transaction ID
        transaction_id = generate_id("TRX")
        
        self.assertIsNotNone(transaction_id)
        self.assertTrue(transaction_id.startswith("TRX"))
        self.assertEqual(len(transaction_id), 10)  # "TRX" + 7 chars


class TestEncryption(unittest.TestCase):
    """Unit tests for encryption utility functions."""
    
    def test_encrypt_decrypt(self):
        """Test encrypting and decrypting data."""
        # Original data
        original_data = "sensitive-data-123"
        
        # Encrypt data
        encrypted_data = encrypt_data(original_data)
        
        self.assertIsNotNone(encrypted_data)
        self.assertNotEqual(encrypted_data, original_data)
        
        # Decrypt data
        decrypted_data = decrypt_data(encrypted_data)
        
        self.assertEqual(decrypted_data, original_data)


class TestValidators(unittest.TestCase):
    """Unit tests for validation utility functions."""
    
    def test_validate_email(self):
        """Test validating email addresses."""
        # Valid email
        self.assertTrue(validate_email("test@example.com"))
        self.assertTrue(validate_email("test.user@example.co.uk"))
        self.assertTrue(validate_email("test+filter@example.com"))
        
        # Invalid email
        self.assertFalse(validate_email("invalid-email"))
        self.assertFalse(validate_email("test@"))
        self.assertFalse(validate_email("@example.com"))
        self.assertFalse(validate_email("test@example"))
    
    def test_validate_phone(self):
        """Test validating phone numbers."""
        # Valid phone
        self.assertTrue(validate_phone("1234567890"))
        self.assertTrue(validate_phone("+1-234-567-8900"))
        self.assertTrue(validate_phone("(123) 456-7890"))
        
        # Invalid phone
        self.assertFalse(validate_phone("123"))
        self.assertFalse(validate_phone("abcdefghij"))
        self.assertFalse(validate_phone(""))
    
    def test_validate_date(self):
        """Test validating dates."""
        # Valid date
        self.assertTrue(validate_date("2023-01-01"))
        self.assertTrue(validate_date("01/01/2023"))
        self.assertTrue(validate_date("Jan 1, 2023"))
        
        # Invalid date
        self.assertFalse(validate_date("invalid-date"))
        self.assertFalse(validate_date("2023-13-01"))
        self.assertFalse(validate_date("2023-01-32"))


class TestDateFormat(unittest.TestCase):
    """Unit tests for date formatting utility functions."""
    
    def test_format_date(self):
        """Test formatting dates."""
        # Format ISO date
        formatted_date = format_date("2023-01-01")
        
        self.assertIsNotNone(formatted_date)
        self.assertIn("2023", formatted_date)
        self.assertIn("01", formatted_date)
        
        # Format with custom format
        custom_formatted_date = format_date("2023-01-01", "%d-%m-%Y")
        
        self.assertEqual(custom_formatted_date, "01-01-2023")
    
    def test_parse_date(self):
        """Test parsing dates."""
        # Parse ISO date
        parsed_date = parse_date("2023-01-01")
        
        self.assertIsNotNone(parsed_date)
        self.assertEqual(parsed_date.year, 2023)
        self.assertEqual(parsed_date.month, 1)
        self.assertEqual(parsed_date.day, 1)
        
        # Parse with custom format
        custom_parsed_date = parse_date("01/01/2023", "%d/%m/%Y")
        
        self.assertEqual(custom_parsed_date.year, 2023)
        self.assertEqual(custom_parsed_date.month, 1)
        self.assertEqual(custom_parsed_date.day, 1)


if __name__ == "__main__":
    unittest.main()
