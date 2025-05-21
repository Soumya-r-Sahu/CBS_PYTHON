"""
Core Banking Payment Integration Tests

This module contains integration tests for payment-related functionality.
These tests verify that payment components work together correctly.
"""

import pytest
import unittest
import sys
from pathlib import Path
from unittest import mock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import payment modules
from payments.upi.processor import process_upi_payment
from payments.neft.processor import process_neft_payment
from payments.imps.processor import process_imps_payment

# Import account and transaction modules
from database.python.common.database_operations import Account, Transaction
from database.db_manager import get_db_session


class TestPaymentIntegration(unittest.TestCase):
    """Integration tests for payment processing."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database session."""
        cls.db_session = get_db_session()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database session."""
        cls.db_session.close()
    
    def setUp(self):
        """Set up before each test."""
        # Begin a transaction
        self.transaction = self.db_session.begin_nested()
        
        # Create test accounts
        self.source_account = Account(
            account_id="ACC_SRC_TEST",
            customer_id="CUS_TEST",
            account_type="SAVINGS",
            balance=10000.00,
            currency="USD",
            status="ACTIVE"
        )
        
        self.destination_account = Account(
            account_id="ACC_DST_TEST",
            customer_id="CUS_TEST_2",
            account_type="SAVINGS",
            balance=5000.00,
            currency="USD",
            status="ACTIVE"
        )
        
        # Add accounts to database
        self.db_session.add(self.source_account)
        self.db_session.add(self.destination_account)
        self.db_session.flush()
    
    def tearDown(self):
        """Clean up after each test."""
        # Roll back the transaction
        self.transaction.rollback()
    
    @mock.patch('payments.neft.processor.send_neft_request')
    def test_neft_payment_integration(self, mock_send):
        """Test NEFT payment integration."""
        # Configure mock
        mock_send.return_value = {
            "status": "SUCCESS",
            "reference_id": "NEFT_INT_TEST",
            "timestamp": "2023-01-01T12:00:00"
        }
        
        # Initial balances
        source_initial_balance = self.source_account.balance
        destination_initial_balance = self.destination_account.balance
        
        # Payment details
        payment_amount = 1000.00
        payment_details = {
            "source_account": self.source_account.account_id,
            "destination_account": self.destination_account.account_id,
            "destination_ifsc": "HDFC0001234",
            "amount": payment_amount,
            "description": "Test NEFT Payment",
            "session": self.db_session  # Pass session for testing
        }
        
        # Process payment
        result = process_neft_payment(payment_details)
        
        # Verify result
        self.assertEqual(result["status"], "SUCCESS")
        
        # Get updated accounts
        updated_source = self.db_session.query(Account).filter_by(
            account_id=self.source_account.account_id
        ).first()
        
        updated_destination = self.db_session.query(Account).filter_by(
            account_id=self.destination_account.account_id
        ).first()
        
        # Verify balances were updated
        self.assertEqual(updated_source.balance, source_initial_balance - payment_amount)
        self.assertEqual(updated_destination.balance, destination_initial_balance + payment_amount)
        
        # Verify transactions were created
        source_transaction = self.db_session.query(Transaction).filter_by(
            account_id=self.source_account.account_id
        ).first()
        
        destination_transaction = self.db_session.query(Transaction).filter_by(
            account_id=self.destination_account.account_id
        ).first()
        
        self.assertIsNotNone(source_transaction)
        self.assertIsNotNone(destination_transaction)
        self.assertEqual(source_transaction.amount, payment_amount)
        self.assertEqual(destination_transaction.amount, payment_amount)
        self.assertEqual(source_transaction.transaction_type, "NEFT_OUTWARD")
        self.assertEqual(destination_transaction.transaction_type, "NEFT_INWARD")
    
    @mock.patch('payments.imps.processor.send_imps_request')
    def test_imps_payment_integration(self, mock_send):
        """Test IMPS payment integration."""
        # Configure mock
        mock_send.return_value = {
            "status": "SUCCESS",
            "reference_id": "IMPS_INT_TEST",
            "timestamp": "2023-01-01T12:00:00"
        }
        
        # Initial balances
        source_initial_balance = self.source_account.balance
        destination_initial_balance = self.destination_account.balance
        
        # Payment details
        payment_amount = 1000.00
        payment_details = {
            "source_account": self.source_account.account_id,
            "destination_account": self.destination_account.account_id,
            "destination_ifsc": "HDFC0001234",
            "amount": payment_amount,
            "description": "Test IMPS Payment",
            "session": self.db_session  # Pass session for testing
        }
        
        # Process payment
        result = process_imps_payment(payment_details)
        
        # Verify result
        self.assertEqual(result["status"], "SUCCESS")
        
        # Get updated accounts
        updated_source = self.db_session.query(Account).filter_by(
            account_id=self.source_account.account_id
        ).first()
        
        updated_destination = self.db_session.query(Account).filter_by(
            account_id=self.destination_account.account_id
        ).first()
        
        # Verify balances were updated
        self.assertEqual(updated_source.balance, source_initial_balance - payment_amount)
        self.assertEqual(updated_destination.balance, destination_initial_balance + payment_amount)
        
        # Verify transactions were created
        source_transaction = self.db_session.query(Transaction).filter_by(
            account_id=self.source_account.account_id
        ).first()
        
        destination_transaction = self.db_session.query(Transaction).filter_by(
            account_id=self.destination_account.account_id
        ).first()
        
        self.assertIsNotNone(source_transaction)
        self.assertIsNotNone(destination_transaction)
        self.assertEqual(source_transaction.transaction_type, "IMPS_OUTWARD")
        self.assertEqual(destination_transaction.transaction_type, "IMPS_INWARD")
    
    @mock.patch('payments.upi.processor.send_upi_request')
    def test_upi_payment_integration(self, mock_send):
        """Test UPI payment integration."""
        # Configure mock
        mock_send.return_value = {
            "status": "SUCCESS",
            "reference_id": "UPI_INT_TEST",
            "timestamp": "2023-01-01T12:00:00"
        }
        
        # Set up UPI IDs for accounts
        self.source_account.upi_id = "source@upi"
        self.destination_account.upi_id = "destination@upi"
        self.db_session.flush()
        
        # Initial balances
        source_initial_balance = self.source_account.balance
        destination_initial_balance = self.destination_account.balance
        
        # Payment details
        payment_amount = 500.00
        payment_details = {
            "source_vpa": self.source_account.upi_id,
            "destination_vpa": self.destination_account.upi_id,
            "amount": payment_amount,
            "description": "Test UPI Payment",
            "session": self.db_session  # Pass session for testing
        }
        
        # Process payment
        result = process_upi_payment(payment_details)
        
        # Verify result
        self.assertEqual(result["status"], "SUCCESS")
        
        # Get updated accounts
        updated_source = self.db_session.query(Account).filter_by(
            account_id=self.source_account.account_id
        ).first()
        
        updated_destination = self.db_session.query(Account).filter_by(
            account_id=self.destination_account.account_id
        ).first()
        
        # Verify balances were updated
        self.assertEqual(updated_source.balance, source_initial_balance - payment_amount)
        self.assertEqual(updated_destination.balance, destination_initial_balance + payment_amount)
        
        # Verify transactions were created
        source_transaction = self.db_session.query(Transaction).filter_by(
            account_id=self.source_account.account_id,
            transaction_type="UPI_OUTWARD"
        ).first()
        
        destination_transaction = self.db_session.query(Transaction).filter_by(
            account_id=self.destination_account.account_id,
            transaction_type="UPI_INWARD"
        ).first()
        
        self.assertIsNotNone(source_transaction)
        self.assertIsNotNone(destination_transaction)
        self.assertEqual(source_transaction.amount, payment_amount)
        self.assertEqual(destination_transaction.amount, payment_amount)


if __name__ == "__main__":
    unittest.main()
