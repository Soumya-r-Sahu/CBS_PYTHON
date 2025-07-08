"""
ATM End-to-End Integration Tests

This module contains end-to-end integration tests for the ATM Switch module.
These tests verify that all components work together correctly.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

# Import required components
from digital_channels.atm_switch.domain.entities.atm_card import AtmCard
from digital_channels.atm_switch.domain.entities.atm_session import AtmSession
from digital_channels.atm_switch.domain.entities.transaction import Transaction
from digital_channels.atm_switch.application.services.atm_service import AtmService
from digital_channels.atm_switch.di_container import get_atm_service

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class AtmIntegrationTests(unittest.TestCase):
    """Integration tests for ATM Switch module"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a mock repository to simulate database
        self.mock_repository = MagicMock()
        self.mock_notification = MagicMock()
        
        # Mock the DI container to use our mock repository
        with patch('digital_channels.atm_switch.di_container.AtmRepository', return_value=self.mock_repository), \
             patch('digital_channels.atm_switch.di_container.NotificationService', return_value=self.mock_notification):
            self.atm_service = get_atm_service()
        
        # Set up test data
        self.test_card = {
            'card_number': '1234567890123456',
            'pin_hash': 'hashed_1234',  # In real tests, use proper hashing
            'account_number': '9876543210',
            'expiry_date': '12/25',
            'status': 'active',
            'daily_withdrawal_limit': Decimal('1000.00'),
            'daily_withdrawal_count': 0
        }
        
        self.test_account = {
            'account_number': '9876543210',
            'customer_id': 'CUST123',
            'account_type': 'savings',
            'status': 'active',
            'available_balance': Decimal('5000.00'),
            'ledger_balance': Decimal('5000.00'),
            'currency': 'USD'
        }
        
        # Set up repository mocks
        self.mock_repository.get_card_by_number.return_value = self.test_card
        self.mock_repository.validate_pin.return_value = True
        self.mock_repository.get_account_by_number.return_value = self.test_account
        self.mock_repository.create_session.return_value = "test_session_token"
        
    def test_end_to_end_atm_flow(self):
        """Test a complete ATM flow: login, check balance, withdraw, get statement, logout"""
        
        # Step 1: Login
        login_response = self.atm_service.login('1234567890123456', '1234')
        self.assertTrue(login_response['success'])
        self.assertEqual(login_response['data']['account_number'], '9876543210')
        session_token = login_response['data']['session_token']
        
        # Step 2: Check Balance
        balance_response = self.atm_service.check_balance(session_token)
        self.assertTrue(balance_response['success'])
        self.assertEqual(balance_response['data']['available_balance'], Decimal('5000.00'))
        
        # Step 3: Withdraw Cash
        # Set up withdrawal response
        self.mock_repository.update_account_balance.return_value = {
            'available_balance': Decimal('4900.00'),
            'ledger_balance': Decimal('4900.00')
        }
        self.mock_repository.create_transaction.return_value = {
            'transaction_id': 'TXN123',
            'timestamp': 1621234567.89
        }
        
        withdraw_response = self.atm_service.withdraw(session_token, Decimal('100.00'))
        self.assertTrue(withdraw_response['success'])
        self.assertEqual(withdraw_response['data']['available_balance'], Decimal('4900.00'))
        self.assertEqual(withdraw_response['data']['transaction_id'], 'TXN123')
        
        # Step 4: Get Mini Statement
        # Set up mini statement response
        self.mock_repository.get_recent_transactions.return_value = [
            {
                'transaction_id': 'TXN123', 
                'timestamp': 1621234567.89,
                'amount': Decimal('100.00'),
                'type': 'withdrawal',
                'description': 'ATM Withdrawal',
                'balance': Decimal('4900.00')
            },
            {
                'transaction_id': 'TXN122', 
                'timestamp': 1621234000.00,
                'amount': Decimal('500.00'),
                'type': 'deposit',
                'description': 'Salary Deposit',
                'balance': Decimal('5000.00')
            }
        ]
        
        statement_response = self.atm_service.get_mini_statement(session_token)
        self.assertTrue(statement_response['success'])
        self.assertEqual(len(statement_response['data']['transactions']), 2)
        self.assertEqual(statement_response['data']['available_balance'], Decimal('4900.00'))
        
        # Step 5: Logout
        logout_response = self.atm_service.logout(session_token)
        self.assertTrue(logout_response['success'])
        
        # Verify session was invalidated
        self.mock_repository.invalidate_session.assert_called_once_with(session_token)

    def test_invalid_card_login(self):
        """Test login with invalid card"""
        self.mock_repository.get_card_by_number.return_value = None
        
        response = self.atm_service.login('9999999999999999', '1234')
        self.assertFalse(response['success'])
        self.assertEqual(response['error_code'], 'invalid_card')

    def test_withdrawal_exceeding_limit(self):
        """Test withdrawal exceeding daily limit"""
        # Login
        login_response = self.atm_service.login('1234567890123456', '1234')
        session_token = login_response['data']['session_token']
        
        # Set up card with near-limit usage
        self.mock_repository.get_card_from_session.return_value = {
            'card_number': '1234567890123456',
            'daily_withdrawal_limit': Decimal('1000.00'),
            'daily_withdrawal_count': 2,
            'daily_withdrawal_amount': Decimal('900.00')
        }
        
        # Try to withdraw more than the remaining limit
        withdraw_response = self.atm_service.withdraw(session_token, Decimal('200.00'))
        self.assertFalse(withdraw_response['success'])
        self.assertEqual(withdraw_response['error_code'], 'limit_exceeded')
        
    def test_insufficient_funds(self):
        """Test withdrawal with insufficient funds"""
        # Login
        login_response = self.atm_service.login('1234567890123456', '1234')
        session_token = login_response['data']['session_token']
        
        # Set up account with low balance
        low_balance_account = dict(self.test_account)
        low_balance_account['available_balance'] = Decimal('50.00')
        self.mock_repository.get_account_from_session.return_value = low_balance_account
        
        # Try to withdraw more than available
        withdraw_response = self.atm_service.withdraw(session_token, Decimal('100.00'))
        self.assertFalse(withdraw_response['success'])
        self.assertEqual(withdraw_response['error_code'], 'insufficient_funds')


if __name__ == "__main__":
    unittest.main()
