"""
Core Banking Digital Channels Unit Tests

This module contains unit tests for digital channel components like
Internet Banking, Mobile Banking, and ATM services.
"""

import pytest
import unittest
from unittest import mock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import digital channels modules
from digital_channels.internet_banking.auth import verify_credentials, generate_otp
from digital_channels.internet_banking.session import create_session, validate_session
from digital_channels.mobile_banking.auth import verify_mobile_credentials
from digital_channels.atm_switch.transaction_processor import process_atm_transaction


class TestInternetBankingAuth(unittest.TestCase):
    """Unit tests for Internet Banking authentication."""
    
    @mock.patch('digital_channels.internet_banking.auth.validate_user_credentials')
    def test_verify_credentials_valid(self, mock_validate):
        """Test verifying valid credentials."""
        # Configure mock
        mock_validate.return_value = True
        
        # Test data
        credentials = {
            "username": "test_user",
            "password": "secure_password"
        }
        
        # Verify credentials
        result = verify_credentials(credentials["username"], credentials["password"])
        
        # Check result
        self.assertTrue(result)
        mock_validate.assert_called_once_with(credentials["username"], credentials["password"])
    
    @mock.patch('digital_channels.internet_banking.auth.validate_user_credentials')
    def test_verify_credentials_invalid(self, mock_validate):
        """Test verifying invalid credentials."""
        # Configure mock
        mock_validate.return_value = False
        
        # Test data
        credentials = {
            "username": "test_user",
            "password": "wrong_password"
        }
        
        # Verify credentials
        result = verify_credentials(credentials["username"], credentials["password"])
        
        # Check result
        self.assertFalse(result)
        mock_validate.assert_called_once_with(credentials["username"], credentials["password"])
    
    @mock.patch('digital_channels.internet_banking.auth.send_otp')
    def test_generate_otp(self, mock_send):
        """Test generating and sending OTP."""
        # Configure mock
        mock_send.return_value = True
        
        # Generate OTP
        result = generate_otp("test_user", "phone")
        
        # Check result
        self.assertTrue(result["success"])
        self.assertTrue("otp_reference" in result)
        self.assertEqual(len(result["otp_reference"]), 32)  # UUID format
        mock_send.assert_called_once()


class TestInternetBankingSession(unittest.TestCase):
    """Unit tests for Internet Banking session management."""
    
    @mock.patch('digital_channels.internet_banking.session.generate_session_token')
    def test_create_session(self, mock_generate):
        """Test creating a new session."""
        # Configure mock
        session_token = "abcdef1234567890"
        mock_generate.return_value = session_token
        
        # Create session
        user_id = "test_user"
        session = create_session(user_id)
        
        # Check session
        self.assertEqual(session["user_id"], user_id)
        self.assertEqual(session["token"], session_token)
        self.assertTrue("expiry" in session)
        mock_generate.assert_called_once()
    
    @mock.patch('digital_channels.internet_banking.session.lookup_session')
    def test_validate_valid_session(self, mock_lookup):
        """Test validating a valid session."""
        # Configure mock
        mock_session = {
            "user_id": "test_user",
            "token": "abcdef1234567890",
            "expiry": 1715012345,  # Future time
            "active": True
        }
        mock_lookup.return_value = mock_session
        
        # Validate session
        result = validate_session("abcdef1234567890")
        
        # Check result
        self.assertTrue(result["valid"])
        self.assertEqual(result["user_id"], "test_user")
        mock_lookup.assert_called_once_with("abcdef1234567890")
    
    @mock.patch('digital_channels.internet_banking.session.lookup_session')
    def test_validate_expired_session(self, mock_lookup):
        """Test validating an expired session."""
        # Configure mock - expired session
        mock_session = {
            "user_id": "test_user",
            "token": "abcdef1234567890",
            "expiry": 1525012345,  # Past time
            "active": True
        }
        mock_lookup.return_value = mock_session
        
        # Validate session
        result = validate_session("abcdef1234567890")
        
        # Check result
        self.assertFalse(result["valid"])
        self.assertEqual(result["error"], "Session expired")
        mock_lookup.assert_called_once_with("abcdef1234567890")


class TestMobileBankingAuth(unittest.TestCase):
    """Unit tests for Mobile Banking authentication."""
    
    @mock.patch('digital_channels.mobile_banking.auth.validate_mobile_device')
    @mock.patch('digital_channels.mobile_banking.auth.validate_user_credentials')
    def test_verify_mobile_credentials_valid(self, mock_validate_creds, mock_validate_device):
        """Test verifying valid mobile credentials."""
        # Configure mocks
        mock_validate_creds.return_value = True
        mock_validate_device.return_value = True
        
        # Test data
        credentials = {
            "username": "mobile_user",
            "password": "secure_password",
            "device_id": "device123"
        }
        
        # Verify credentials
        result = verify_mobile_credentials(
            credentials["username"], 
            credentials["password"], 
            credentials["device_id"]
        )
        
        # Check result
        self.assertTrue(result["authenticated"])
        self.assertFalse("error" in result)
        mock_validate_creds.assert_called_once()
        mock_validate_device.assert_called_once()
    
    @mock.patch('digital_channels.mobile_banking.auth.validate_mobile_device')
    def test_verify_mobile_credentials_invalid_device(self, mock_validate_device):
        """Test verifying credentials with an invalid device."""
        # Configure mock
        mock_validate_device.return_value = False
        
        # Test data
        credentials = {
            "username": "mobile_user",
            "password": "secure_password",
            "device_id": "unknown_device"
        }
        
        # Verify credentials
        result = verify_mobile_credentials(
            credentials["username"], 
            credentials["password"], 
            credentials["device_id"]
        )
        
        # Check result
        self.assertFalse(result["authenticated"])
        self.assertEqual(result["error"], "Device not recognized")
        mock_validate_device.assert_called_once()


class TestATMTransactions(unittest.TestCase):
    """Unit tests for ATM transaction processing."""
    
    @mock.patch('digital_channels.atm_switch.transaction_processor.validate_card')
    @mock.patch('digital_channels.atm_switch.transaction_processor.validate_pin')
    @mock.patch('digital_channels.atm_switch.transaction_processor.process_withdrawal')
    def test_process_withdrawal_transaction(self, mock_withdrawal, mock_pin, mock_card):
        """Test processing a withdrawal transaction."""
        # Configure mocks
        mock_card.return_value = {"valid": True, "account_id": "ACC123456"}
        mock_pin.return_value = True
        mock_withdrawal.return_value = {
            "success": True,
            "transaction_id": "ATM123456",
            "amount": 200.00,
            "balance": 800.00
        }
        
        # Transaction data
        transaction = {
            "transaction_type": "WITHDRAWAL",
            "card_number": "1234567890123456",
            "pin": "1234",
            "amount": 200.00,
            "atm_id": "ATM001"
        }
        
        # Process transaction
        result = process_atm_transaction(transaction)
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["transaction_id"], "ATM123456")
        self.assertEqual(result["amount"], 200.00)
        self.assertEqual(result["balance"], 800.00)
        mock_card.assert_called_once_with(transaction["card_number"])
        mock_pin.assert_called_once_with(transaction["card_number"], transaction["pin"])
        mock_withdrawal.assert_called_once()
    
    @mock.patch('digital_channels.atm_switch.transaction_processor.validate_card')
    @mock.patch('digital_channels.atm_switch.transaction_processor.validate_pin')
    def test_process_transaction_invalid_pin(self, mock_pin, mock_card):
        """Test processing a transaction with an invalid PIN."""
        # Configure mocks
        mock_card.return_value = {"valid": True, "account_id": "ACC123456"}
        mock_pin.return_value = False
        
        # Transaction data
        transaction = {
            "transaction_type": "WITHDRAWAL",
            "card_number": "1234567890123456",
            "pin": "wrong_pin",
            "amount": 200.00,
            "atm_id": "ATM001"
        }
        
        # Process transaction
        result = process_atm_transaction(transaction)
        
        # Check result
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid PIN")
        mock_card.assert_called_once_with(transaction["card_number"])
        mock_pin.assert_called_once_with(transaction["card_number"], transaction["pin"])


if __name__ == "__main__":
    unittest.main()
