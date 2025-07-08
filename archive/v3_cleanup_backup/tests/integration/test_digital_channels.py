"""
Core Banking Digital Channels Integration Tests

This module contains integration tests for digital channels like
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
from digital_channels.internet_banking.transaction import process_transaction
from digital_channels.mobile_banking.auth import verify_mobile_credentials
from digital_channels.mobile_banking.transaction import process_mobile_transaction

# Import database modules
from database.python.models import Account, Transaction, Customer
from database.db_manager import get_db_session


class TestInternetBankingIntegration(unittest.TestCase):
    """Integration tests for Internet Banking services."""
    
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
        
        # Create test customer and accounts
        self.customer = Customer(
            customer_id="CUS_IB_TEST",
            first_name="Internet",
            last_name="Banking",
            email="internet.banking@example.com",
            username="ibtest",
            password_hash="hashed_password",  # Pre-hashed password
            status="ACTIVE"
        )
        
        self.source_account = Account(
            account_id="ACC_IB_SRC",
            customer_id="CUS_IB_TEST",
            account_type="SAVINGS",
            balance=10000.00,
            currency="USD",
            status="ACTIVE"
        )
        
        self.destination_account = Account(
            account_id="ACC_IB_DST",
            customer_id="CUS_IB_TEST",
            account_type="CURRENT",
            balance=5000.00,
            currency="USD",
            status="ACTIVE"
        )
        
        # Add to database
        self.db_session.add(self.customer)
        self.db_session.add(self.source_account)
        self.db_session.add(self.destination_account)
        self.db_session.flush()
    
    def tearDown(self):
        """Clean up after each test."""
        # Roll back the transaction
        self.transaction.rollback()
    
    @mock.patch('digital_channels.internet_banking.auth.validate_password_hash')
    def test_authentication_and_transaction_flow(self, mock_validate):
        """Test full flow from authentication to transaction in Internet Banking."""
        # Configure mock for password validation
        mock_validate.return_value = True
        
        # Step 1: Authenticate user
        auth_result = verify_credentials("ibtest", "correct_password")
        self.assertTrue(auth_result)
        
        # Step 2: Create session
        session = create_session("ibtest")
        self.assertEqual(session["user_id"], "ibtest")
        self.assertTrue("token" in session)
        
        # Step 3: Make transfer
        transaction_data = {
            "session_token": session["token"],
            "transaction_type": "TRANSFER",
            "source_account": "ACC_IB_SRC",
            "destination_account": "ACC_IB_DST",
            "amount": 1000.00,
            "description": "Test transfer",
            "db_session": self.db_session  # For testing
        }
        
        # Process transaction
        result = process_transaction(transaction_data)
        
        # Verify transaction was successful
        self.assertTrue(result["success"])
        self.assertTrue("transaction_id" in result)
        
        # Verify account balances were updated
        updated_source = self.db_session.query(Account).filter_by(
            account_id="ACC_IB_SRC"
        ).first()
        
        updated_dest = self.db_session.query(Account).filter_by(
            account_id="ACC_IB_DST"
        ).first()
        
        self.assertEqual(updated_source.balance, 9000.00)
        self.assertEqual(updated_dest.balance, 6000.00)
        
        # Verify transactions were created
        transactions = self.db_session.query(Transaction).filter(
            (Transaction.account_id == "ACC_IB_SRC") | 
            (Transaction.account_id == "ACC_IB_DST")
        ).all()
        
        self.assertEqual(len(transactions), 2)  # One for each account


class TestMobileBankingIntegration(unittest.TestCase):
    """Integration tests for Mobile Banking services."""
    
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
        
        # Create test customer and account
        self.customer = Customer(
            customer_id="CUS_MB_TEST",
            first_name="Mobile",
            last_name="Banking",
            email="mobile.banking@example.com",
            username="mbtest",
            password_hash="hashed_password",  # Pre-hashed password
            status="ACTIVE"
        )
        
        self.account = Account(
            account_id="ACC_MB_TEST",
            customer_id="CUS_MB_TEST",
            account_type="SAVINGS",
            balance=5000.00,
            currency="USD",
            status="ACTIVE"
        )
        
        # Add to database
        self.db_session.add(self.customer)
        self.db_session.add(self.account)
        self.db_session.flush()
        
        # Add mobile device
        from digital_channels.mobile_banking.device import register_device
        
        register_device({
            "customer_id": "CUS_MB_TEST",
            "device_id": "DEVICE123",
            "device_type": "ANDROID",
            "registration_date": "2023-01-01",
            "db_session": self.db_session  # For testing
        })
    
    def tearDown(self):
        """Clean up after each test."""
        # Roll back the transaction
        self.transaction.rollback()
    
    @mock.patch('digital_channels.mobile_banking.auth.validate_password_hash')
    def test_mobile_bill_payment_flow(self, mock_validate):
        """Test the bill payment flow from mobile banking."""
        # Configure mock for password validation
        mock_validate.return_value = True
        
        # Step 1: Authenticate
        auth_result = verify_mobile_credentials("mbtest", "correct_password", "DEVICE123")
        self.assertTrue(auth_result["authenticated"])
        
        # Step 2: Pay bill
        bill_payment = {
            "customer_id": "CUS_MB_TEST",
            "account_id": "ACC_MB_TEST",
            "biller_id": "UTIL123",
            "consumer_number": "987654321",
            "amount": 100.00,
            "biller_name": "Electricity Company",
            "reference_number": "BILL123",
            "db_session": self.db_session  # For testing
        }
        
        # Process bill payment
        result = process_mobile_transaction({
            "transaction_type": "BILL_PAYMENT",
            "data": bill_payment
        })
        
        # Verify payment was successful
        self.assertTrue(result["success"])
        self.assertTrue("transaction_id" in result)
        
        # Verify account balance was updated
        updated_account = self.db_session.query(Account).filter_by(
            account_id="ACC_MB_TEST"
        ).first()
        
        self.assertEqual(updated_account.balance, 4900.00)
        
        # Verify transaction was created
        transaction = self.db_session.query(Transaction).filter_by(
            account_id="ACC_MB_TEST"
        ).first()
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.transaction_type, "BILL_PAYMENT")
        self.assertEqual(transaction.amount, 100.00)
        self.assertEqual(transaction.status, "COMPLETED")


class TestATMIntegration(unittest.TestCase):
    """Integration tests for ATM services."""
    
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
        
        # Create test customer and account
        self.customer = Customer(
            customer_id="CUS_ATM_TEST",
            first_name="ATM",
            last_name="Test",
            email="atm.test@example.com",
            status="ACTIVE"
        )
        
        self.account = Account(
            account_id="ACC_ATM_TEST",
            customer_id="CUS_ATM_TEST",
            account_type="SAVINGS",
            balance=2000.00,
            currency="USD",
            status="ACTIVE"
        )
        
        # Add to database
        self.db_session.add(self.customer)
        self.db_session.add(self.account)
        self.db_session.flush()
        
        # Add card details
        from digital_channels.atm_switch.card_manager import register_card
        
        register_card({
            "card_number": "1234567890123456",
            "account_id": "ACC_ATM_TEST",
            "customer_id": "CUS_ATM_TEST",
            "pin_hash": "hashed_pin",  # Pre-hashed PIN
            "expiry_date": "12/25",
            "status": "ACTIVE",
            "db_session": self.db_session  # For testing
        })
    
    def tearDown(self):
        """Clean up after each test."""
        # Roll back the transaction
        self.transaction.rollback()
    
    @mock.patch('digital_channels.atm_switch.transaction_processor.validate_pin')
    def test_atm_withdrawal_integration(self, mock_validate_pin):
        """Test ATM withdrawal integration."""
        # Configure mock for PIN validation
        mock_validate_pin.return_value = True
        
        # Process ATM withdrawal
        from digital_channels.atm_switch.transaction_processor import process_atm_transaction
        
        transaction = {
            "transaction_type": "WITHDRAWAL",
            "card_number": "1234567890123456",
            "pin": "1234",
            "amount": 500.00,
            "atm_id": "ATM001",
            "db_session": self.db_session  # For testing
        }
        
        result = process_atm_transaction(transaction)
        
        # Verify withdrawal was successful
        self.assertTrue(result["success"])
        self.assertTrue("transaction_id" in result)
        
        # Verify account balance was updated
        updated_account = self.db_session.query(Account).filter_by(
            account_id="ACC_ATM_TEST"
        ).first()
        
        self.assertEqual(updated_account.balance, 1500.00)
        
        # Verify transaction was created
        transaction = self.db_session.query(Transaction).filter_by(
            account_id="ACC_ATM_TEST"
        ).first()
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.transaction_type, "ATM_WITHDRAWAL")
        self.assertEqual(transaction.amount, 500.00)
        self.assertEqual(transaction.status, "COMPLETED")


if __name__ == "__main__":
    unittest.main()
