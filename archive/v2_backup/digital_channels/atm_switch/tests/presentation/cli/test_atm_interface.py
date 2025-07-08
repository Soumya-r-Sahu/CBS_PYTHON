"""
Tests for ATM CLI interface

This module tests the CLI interface for the ATM-Switch module.
"""

import unittest
from unittest.mock import Mock, patch
from decimal import Decimal
import sys
import os

# Add parent directories to path for relative imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from presentation.cli.atm_interface import AtmCli

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class TestAtmCli(unittest.TestCase):
    def setUp(self):
        # Create a mock ATM service
        self.mock_atm_service = Mock()
          # Patch the get_atm_service function to return our mock
        patcher_path = 'digital_channels.atm_switch.di_container.get_atm_service'
        # Fall back to relative import if needed
        try:
            self.patcher = patch(patcher_path)
        except:
            self.patcher = patch('di_container.get_atm_service')
        self.mock_get_service = self.patcher.start()
        self.mock_get_service.return_value = self.mock_atm_service
        
        # Create CLI with mocked service
        self.cli = AtmCli()
    
    def tearDown(self):
        self.patcher.stop()
    
    def test_validate_card_success(self):
        # Arrange
        self.mock_atm_service.login.return_value = {
            'success': True,
            'data': {
                'session_token': 'test_token',
                'account_number': '1234567890'
            }
        }
        
        # Act
        with patch('builtins.input', side_effect=['1234567890', '1234']):
            with patch('builtins.print') as mock_print:
                result = self.cli.validate_card()
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(self.cli.session_token, 'test_token')
        self.assertEqual(self.cli.account_number, '1234567890')
        self.mock_atm_service.login.assert_called_once_with('1234567890', '1234')
    
    def test_validate_card_failure(self):
        # Arrange
        self.mock_atm_service.login.return_value = {
            'success': False,
            'message': 'Invalid card or PIN'
        }
          # Act
        with patch('builtins.input', side_effect=['1234567890', '4321']):
            with patch('builtins.print') as mock_print:
                result = self.cli.validate_card()
        
        # Assert
        self.assertFalse(result)
        self.assertIsNone(self.cli.session_token)
        self.mock_atm_service.login.assert_called_once_with('1234567890', '4321')
        
    def test_check_balance_no_session(self):
        # Arrange
        self.cli.session_token = None
        
        # Act
        with patch('builtins.print') as mock_print:
            self.cli.check_balance()
        
        # Assert
        mock_print.assert_any_call("\nPlease insert card and enter PIN first.")
        self.mock_atm_service.get_balance.assert_not_called()
    
    def test_check_balance_success(self):
        # Arrange
        self.cli.session_token = 'test_token'
        self.cli.account_number = '1234567890'
        self.mock_atm_service.get_balance.return_value = {
            'success': True,
            'data': {
                'balance': Decimal('1000.00'),
                'ledger_balance': Decimal('950.00')
            }
        }
        
        # Act
        with patch('builtins.print') as mock_print:
            self.cli.check_balance()
        
        # Assert
        self.mock_atm_service.get_balance.assert_called_once_with('test_token')
        mock_print.assert_any_call("\nAccount Information:")
        
    def test_withdraw_cash_success(self):
        # Arrange
        self.cli.session_token = 'test_token'
        self.mock_atm_service.withdraw.return_value = {
            'success': True,
            'data': {
                'amount': Decimal('100.00'),
                'fee': Decimal('2.50'),
                'total': Decimal('102.50'),
                'balance': Decimal('897.50'),
                'transaction_id': '12345'
            }
        }
        
        # Act
        with patch('builtins.input', return_value='100.00'):
            with patch('builtins.print') as mock_print:
                self.cli.withdraw_cash()
        
        # Assert
        self.mock_atm_service.withdraw.assert_called_once_with('test_token', Decimal('100.00'))
        mock_print.assert_any_call("\nWithdrawal successful!")
        
    def test_withdraw_cash_no_session(self):
        # Arrange
        self.cli.session_token = None
        
        # Act
        with patch('builtins.print') as mock_print:
            self.cli.withdraw_cash()
        
        # Assert
        mock_print.assert_any_call("\nPlease insert card and enter PIN first.")
        self.mock_atm_service.withdraw.assert_not_called()
        
    def test_withdraw_cash_invalid_amount(self):
        # Arrange
        self.cli.session_token = 'test_token'
        
        # Act
        with patch('builtins.input', return_value='invalid'):
            with patch('builtins.print') as mock_print:
                self.cli.withdraw_cash()
        
        # Assert
        self.mock_atm_service.withdraw.assert_not_called()
        mock_print.assert_any_call("\nInvalid amount format. Please enter a valid number.")


if __name__ == '__main__':
    unittest.main()
