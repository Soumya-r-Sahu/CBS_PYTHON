"""
ATM CLI Interface Tests

This module contains tests for the ATM CLI interface.
"""

import unittest
from unittest.mock import patch, MagicMock
import io
import sys
import time
from decimal import Decimal

from ....presentation.cli.atm_interface import AtmCli

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class AtmCliTests(unittest.TestCase):
    """Test cases for ATM CLI interface"""

    def setUp(self):
        """Set up test case"""
        # Mock ATM service
        self.mock_atm_service = MagicMock()
        
        # Create ATM CLI with mocked service
        with patch('digital_channels.atm-switch.presentation.cli.atm_interface.get_atm_service', 
                  return_value=self.mock_atm_service):
            self.cli = AtmCli()
    
    def test_validate_input_card_number(self):
        """Test validation of card numbers"""
        # Valid card number
        self.assertTrue(self.cli.validate_input("1234567890123456", "card_number"))
        
        # Invalid card numbers
        self.assertFalse(self.cli.validate_input("123456", "card_number"))  # Too short
        self.assertFalse(self.cli.validate_input("12345678901234567890", "card_number"))  # Too long
        self.assertFalse(self.cli.validate_input("1234-5678-9012-3456", "card_number"))  # Contains hyphens
        self.assertFalse(self.cli.validate_input("abcdefghijklmnop", "card_number"))  # Contains letters
    
    def test_validate_input_pin(self):
        """Test validation of PINs"""
        # Valid PINs
        self.assertTrue(self.cli.validate_input("1234", "pin"))
        self.assertTrue(self.cli.validate_input("123456", "pin"))
        
        # Invalid PINs
        self.assertFalse(self.cli.validate_input("123", "pin"))  # Too short
        self.assertFalse(self.cli.validate_input("1234567", "pin"))  # Too long
        self.assertFalse(self.cli.validate_input("abcd", "pin"))  # Contains letters
    
    def test_validate_input_amount(self):
        """Test validation of amounts"""
        # Valid amounts
        self.assertTrue(self.cli.validate_input("10", "amount"))
        self.assertTrue(self.cli.validate_input("100", "amount"))
        
        # Invalid amounts
        self.assertFalse(self.cli.validate_input("0", "amount"))  # Zero
        self.assertFalse(self.cli.validate_input("-10", "amount"))  # Negative
        self.assertFalse(self.cli.validate_input("15", "amount"))  # Not multiple of 10
        self.assertFalse(self.cli.validate_input("abc", "amount"))  # Not a number
    
    def test_session_timeout(self):
        """Test session timeout handling"""
        # Set up a valid session
        self.cli.session_token = "test_token"
        self.cli.account_number = "1234567890"
        self.cli.last_activity_time = time.time()
        
        # Session should be valid
        self.assertTrue(self.cli.is_session_valid())
        
        # Set last activity to more than timeout seconds ago
        self.cli.last_activity_time = time.time() - self.cli.session_timeout - 10
        
        # Session should now be invalid
        self.assertFalse(self.cli.is_session_valid())
        
        # Session data should be cleared
        self.assertIsNone(self.cli.session_token)
        self.assertIsNone(self.cli.account_number)
        self.assertIsNone(self.cli.last_activity_time)
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_format_currency(self, mock_stdout):
        """Test currency formatting"""
        # Test formatting of various amounts
        self.assertEqual(self.cli.format_currency(Decimal('0')), "$0.00")
        self.assertEqual(self.cli.format_currency(Decimal('10.5')), "$10.50")
        self.assertEqual(self.cli.format_currency(Decimal('1000')), "$1,000.00")
        self.assertEqual(self.cli.format_currency(Decimal('1234567.89')), "$1,234,567.89")
    
    def test_validate_card(self):
        """Test card validation with mocked service"""
        # Mock successful login response
        self.mock_atm_service.login.return_value = {
            'success': True,
            'data': {
                'session_token': 'test_token',
                'account_number': '1234567890123456'
            }
        }
        
        # Mock user input for card number and PIN
        with patch('builtins.input', side_effect=["1234567890123456", "1234"]):
            result = self.cli.validate_card()
            
            # Check that validation was successful
            self.assertTrue(result)
            self.assertEqual(self.cli.session_token, "test_token")
            self.assertEqual(self.cli.account_number, "1234567890123456")
            self.assertIsNotNone(self.cli.last_activity_time)
            
            # Verify service was called with correct parameters
            self.mock_atm_service.login.assert_called_once_with("1234567890123456", "1234")

    def test_logout(self):
        """Test logout functionality"""
        # Set up a valid session
        self.cli.session_token = "test_token"
        self.cli.account_number = "1234567890"
        self.cli.last_activity_time = time.time()
        
        # Logout
        self.cli.logout()
        
        # Verify service call
        self.mock_atm_service.logout.assert_called_once_with("test_token")
        
        # Verify session data is cleared
        self.assertIsNone(self.cli.session_token)
        self.assertIsNone(self.cli.account_number)
        self.assertIsNone(self.cli.last_activity_time)


if __name__ == "__main__":
    unittest.main()
