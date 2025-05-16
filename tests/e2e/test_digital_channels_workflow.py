"""
Core Banking Digital Channels End-to-End Tests

This module contains E2E tests for digital channels workflows including
Internet Banking, Mobile Banking, and ATM-based banking operations.
"""

import unittest
import sys
import requests
import time
import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import utility modules
from database.python.models import Customer, Account, Transaction, Card
from database.db_manager import get_db_session

# Import digital channels modules
from digital_channels.internet_banking.api import create_user, login
from digital_channels.internet_banking.transaction import process_transaction
from digital_channels.mobile_banking.api import register_mobile, login_mobile
from digital_channels.mobile_banking.transaction import process_mobile_transaction
from digital_channels.atm_switch.card_manager import register_card, activate_card
from digital_channels.atm_switch.transaction_processor import process_atm_transaction

# Import from utils
from tests.e2e.db_workflow_utils import (
    create_test_customer,
    create_test_account,
    clean_up_test_data
)


class TestInternetBankingWorkflow(unittest.TestCase):
    """End-to-end tests for Internet Banking workflows."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data for all test methods."""
        cls.db_session = get_db_session()
        
        # Create test customer
        cls.customer = create_test_customer(
            cls.db_session,
            customer_id="E2E_IB_CUST",
            first_name="E2E",
            last_name="IB_Test",
            email="e2e.ib@example.com",
            phone="1234567890"
        )
        
        # Create source and destination accounts
        cls.source_account = create_test_account(
            cls.db_session,
            account_id="E2E_IB_SRC",
            customer_id="E2E_IB_CUST",
            account_type="SAVINGS",
            balance=10000.00
        )
        
        cls.destination_account = create_test_account(
            cls.db_session,
            account_id="E2E_IB_DST",
            customer_id="E2E_IB_CUST",
            account_type="CURRENT",
            balance=5000.00
        )
        
        # Setup for Internet Banking
        username = "e2eibuser"
        password = "Secure@123"
        
        # Create Internet Banking user
        cls.ib_user = create_user({
            "customer_id": "E2E_IB_CUST",
            "username": username,
            "password": password,
            "email": "e2e.ib@example.com",
            "phone": "1234567890",
            "db_session": cls.db_session
        })
        
        cls.username = username
        cls.password = password
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Clean up test data
        clean_up_test_data(cls.db_session, "E2E_IB_CUST")
        cls.db_session.close()
    
    def test_01_login_and_check_accounts(self):
        """Test login and account listing in Internet Banking."""
        # Step 1: Login to Internet Banking
        login_result = login(self.username, self.password, self.db_session)
        
        # Verify login successful
        self.assertTrue(login_result["success"])
        self.assertTrue("session_token" in login_result)
        
        session_token = login_result["session_token"]
        
        # Step 2: Check accounts
        from digital_channels.internet_banking.account import get_accounts
        
        accounts_result = get_accounts({
            "session_token": session_token,
            "db_session": self.db_session
        })
        
        # Verify accounts retrieved successfully
        self.assertTrue(accounts_result["success"])
        self.assertEqual(len(accounts_result["accounts"]), 2)
        
        # Verify account details
        account_ids = [acc["account_id"] for acc in accounts_result["accounts"]]
        self.assertIn("E2E_IB_SRC", account_ids)
        self.assertIn("E2E_IB_DST", account_ids)
        
        # Store session for next test
        self.session_token = session_token
    
    def test_02_fund_transfer(self):
        """Test fund transfer between accounts in Internet Banking."""
        # Check that we have a session token from previous test
        self.assertTrue(hasattr(self, 'session_token'), "No session token available from previous test")
        
        # Step 1: Get account balances before transfer
        from digital_channels.internet_banking.account import get_account_details
        
        source_before = get_account_details({
            "session_token": self.session_token,
            "account_id": "E2E_IB_SRC",
            "db_session": self.db_session
        })
        
        destination_before = get_account_details({
            "session_token": self.session_token,
            "account_id": "E2E_IB_DST",
            "db_session": self.db_session
        })
        
        # Step 2: Execute fund transfer
        transfer_amount = 2000.00
        transaction_data = {
            "session_token": self.session_token,
            "transaction_type": "TRANSFER",
            "source_account": "E2E_IB_SRC",
            "destination_account": "E2E_IB_DST",
            "amount": transfer_amount,
            "description": "E2E Test Transfer",
            "db_session": self.db_session
        }
        
        transfer_result = process_transaction(transaction_data)
        
        # Verify transfer successful
        self.assertTrue(transfer_result["success"])
        self.assertTrue("transaction_id" in transfer_result)
        
        # Step 3: Get account balances after transfer
        source_after = get_account_details({
            "session_token": self.session_token,
            "account_id": "E2E_IB_SRC",
            "db_session": self.db_session
        })
        
        destination_after = get_account_details({
            "session_token": self.session_token,
            "account_id": "E2E_IB_DST",
            "db_session": self.db_session
        })
        
        # Verify balances updated correctly
        self.assertEqual(source_after["account"]["balance"], 
                         source_before["account"]["balance"] - transfer_amount)
        
        self.assertEqual(destination_after["account"]["balance"], 
                         destination_before["account"]["balance"] + transfer_amount)
        
        # Step 4: Check transaction history
        from digital_channels.internet_banking.transaction import get_transaction_history
        
        history_result = get_transaction_history({
            "session_token": self.session_token,
            "account_id": "E2E_IB_SRC",
            "db_session": self.db_session
        })
        
        # Verify transaction in history
        self.assertTrue(history_result["success"])
        transaction_found = False
        for trans in history_result["transactions"]:
            if trans["transaction_id"] == transfer_result["transaction_id"]:
                transaction_found = True
                self.assertEqual(trans["amount"], transfer_amount)
                self.assertEqual(trans["type"], "TRANSFER")
                break
        
        self.assertTrue(transaction_found, "Transaction not found in history")
    
    def test_03_bill_payment(self):
        """Test bill payment in Internet Banking."""
        # Check that we have a session token from previous test
        self.assertTrue(hasattr(self, 'session_token'), "No session token available from previous test")
        
        # Step 1: Get account balance before payment
        from digital_channels.internet_banking.account import get_account_details
        
        account_before = get_account_details({
            "session_token": self.session_token,
            "account_id": "E2E_IB_SRC",
            "db_session": self.db_session
        })
        
        # Step 2: Execute bill payment
        payment_amount = 500.00
        bill_data = {
            "session_token": self.session_token,
            "transaction_type": "BILL_PAYMENT",
            "account_id": "E2E_IB_SRC",
            "biller_id": "UTIL001",
            "biller_name": "Electricity Company",
            "consumer_number": "1234567890",
            "amount": payment_amount,
            "reference": "E2E Bill Test",
            "db_session": self.db_session
        }
        
        payment_result = process_transaction(bill_data)
        
        # Verify payment successful
        self.assertTrue(payment_result["success"])
        self.assertTrue("transaction_id" in payment_result)
        
        # Step 3: Get account balance after payment
        account_after = get_account_details({
            "session_token": self.session_token,
            "account_id": "E2E_IB_SRC",
            "db_session": self.db_session
        })
        
        # Verify balance updated correctly
        self.assertEqual(account_after["account"]["balance"], 
                         account_before["account"]["balance"] - payment_amount)
        
        # Step 4: Check bill payment in transaction history
        from digital_channels.internet_banking.transaction import get_transaction_history
        
        history_result = get_transaction_history({
            "session_token": self.session_token,
            "account_id": "E2E_IB_SRC",
            "db_session": self.db_session
        })
        
        # Verify transaction in history
        self.assertTrue(history_result["success"])
        transaction_found = False
        for trans in history_result["transactions"]:
            if trans["transaction_id"] == payment_result["transaction_id"]:
                transaction_found = True
                self.assertEqual(trans["amount"], payment_amount)
                self.assertEqual(trans["type"], "BILL_PAYMENT")
                self.assertEqual(trans["details"]["biller_id"], "UTIL001")
                break
        
        self.assertTrue(transaction_found, "Bill payment not found in history")


class TestMobileBankingWorkflow(unittest.TestCase):
    """End-to-end tests for Mobile Banking workflows."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data for all test methods."""
        cls.db_session = get_db_session()
        
        # Create test customer
        cls.customer = create_test_customer(
            cls.db_session,
            customer_id="E2E_MB_CUST",
            first_name="E2E",
            last_name="MB_Test",
            email="e2e.mb@example.com",
            phone="1234567891"
        )
        
        # Create accounts
        cls.primary_account = create_test_account(
            cls.db_session,
            account_id="E2E_MB_ACC",
            customer_id="E2E_MB_CUST",
            account_type="SAVINGS",
            balance=15000.00
        )
        
        # Setup for Mobile Banking
        username = "e2embuser"
        password = "Secure@123"
        device_id = "E2E_TEST_DEVICE"
        
        # Register Mobile Banking
        cls.mb_registration = register_mobile({
            "customer_id": "E2E_MB_CUST",
            "username": username,
            "password": password,
            "device_id": device_id,
            "device_type": "Android",
            "phone": "1234567891",
            "db_session": cls.db_session
        })
        
        cls.username = username
        cls.password = password
        cls.device_id = device_id
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Clean up test data
        clean_up_test_data(cls.db_session, "E2E_MB_CUST")
        cls.db_session.close()
    
    def test_01_mobile_login(self):
        """Test login to mobile banking."""
        # Login to Mobile Banking
        login_result = login_mobile(
            self.username,
            self.password,
            self.device_id,
            self.db_session
        )
        
        # Verify login successful
        self.assertTrue(login_result["success"])
        self.assertTrue("session_token" in login_result)
        
        # Store session for next tests
        self.session_token = login_result["session_token"]
    
    def test_02_check_balance(self):
        """Test checking account balance in mobile banking."""
        # Check that we have a session token from previous test
        self.assertTrue(hasattr(self, 'session_token'), "No session token available from previous test")
        
        # Get account balance
        from digital_channels.mobile_banking.account import get_account_balance
        
        balance_result = get_account_balance({
            "session_token": self.session_token,
            "account_id": "E2E_MB_ACC",
            "db_session": self.db_session
        })
        
        # Verify balance check successful
        self.assertTrue(balance_result["success"])
        self.assertEqual(balance_result["account_id"], "E2E_MB_ACC")
        self.assertEqual(balance_result["balance"], 15000.00)
    
    def test_03_mobile_transfer(self):
        """Test transfer to another account via mobile banking."""
        # Check that we have a session token from previous test
        self.assertTrue(hasattr(self, 'session_token'), "No session token available from previous test")
        
        # Create a beneficiary
        from digital_channels.mobile_banking.beneficiary import add_beneficiary
        
        # Create a destination customer and account for transfer
        dest_customer = create_test_customer(
            self.db_session,
            customer_id="E2E_MB_DEST",
            first_name="Destination",
            last_name="User",
            email="dest.user@example.com"
        )
        
        dest_account = create_test_account(
            self.db_session,
            account_id="E2E_MB_DEST_ACC",
            customer_id="E2E_MB_DEST",
            account_type="SAVINGS",
            balance=1000.00
        )
        
        # Add beneficiary
        beneficiary_result = add_beneficiary({
            "session_token": self.session_token,
            "name": "Test Beneficiary",
            "account_number": "E2E_MB_DEST_ACC",
            "account_type": "SAVINGS",
            "ifsc_code": "TEST0001",
            "db_session": self.db_session
        })
        
        # Verify beneficiary added
        self.assertTrue(beneficiary_result["success"])
        
        # Execute transfer
        from digital_channels.mobile_banking.transaction import process_mobile_transaction
        
        transfer_amount = 1000.00
        transfer_data = {
            "transaction_type": "FUND_TRANSFER",
            "data": {
                "session_token": self.session_token,
                "source_account": "E2E_MB_ACC",
                "destination_account": "E2E_MB_DEST_ACC",
                "amount": transfer_amount,
                "remarks": "E2E Mobile Test",
                "db_session": self.db_session
            }
        }
        
        transfer_result = process_mobile_transaction(transfer_data)
        
        # Verify transfer successful
        self.assertTrue(transfer_result["success"])
        
        # Check source account balance
        from digital_channels.mobile_banking.account import get_account_balance
        
        balance_result = get_account_balance({
            "session_token": self.session_token,
            "account_id": "E2E_MB_ACC",
            "db_session": self.db_session
        })
        
        # Verify balance updated
        self.assertEqual(balance_result["balance"], 14000.00)
        
        # Check destination account balance
        dest_account = self.db_session.query(Account).filter_by(
            account_id="E2E_MB_DEST_ACC"
        ).first()
        
        self.assertEqual(dest_account.balance, 2000.00)
        
        # Clean up destination account
        clean_up_test_data(self.db_session, "E2E_MB_DEST")


class TestATMWorkflow(unittest.TestCase):
    """End-to-end tests for ATM transaction workflows."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data for all test methods."""
        cls.db_session = get_db_session()
        
        # Create test customer
        cls.customer = create_test_customer(
            cls.db_session,
            customer_id="E2E_ATM_CUST",
            first_name="E2E",
            last_name="ATM_Test",
            email="e2e.atm@example.com"
        )
        
        # Create account
        cls.account = create_test_account(
            cls.db_session,
            account_id="E2E_ATM_ACC",
            customer_id="E2E_ATM_CUST",
            account_type="SAVINGS",
            balance=20000.00
        )
        
        # Create and activate card
        cls.card_number = "4111111111111111"
        cls.pin = "1234"
        
        card_result = register_card({
            "card_number": cls.card_number,
            "account_id": "E2E_ATM_ACC",
            "customer_id": "E2E_ATM_CUST",
            "pin": cls.pin,
            "expiry_date": "12/25",
            "card_type": "DEBIT",
            "db_session": cls.db_session
        })
        
        activate_card(cls.card_number, cls.db_session)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Clean up test data
        clean_up_test_data(cls.db_session, "E2E_ATM_CUST")
        cls.db_session.close()
    
    def test_01_atm_balance_inquiry(self):
        """Test ATM balance inquiry."""
        # Process balance inquiry
        inquiry_data = {
            "transaction_type": "BALANCE_INQUIRY",
            "card_number": self.card_number,
            "pin": self.pin,
            "atm_id": "ATM001",
            "db_session": self.db_session
        }
        
        inquiry_result = process_atm_transaction(inquiry_data)
        
        # Verify inquiry successful
        self.assertTrue(inquiry_result["success"])
        self.assertEqual(inquiry_result["balance"], 20000.00)
        self.assertEqual(inquiry_result["account_id"], "E2E_ATM_ACC")
    
    def test_02_atm_withdrawal(self):
        """Test ATM cash withdrawal."""
        # Process withdrawal
        withdrawal_amount = 5000.00
        withdrawal_data = {
            "transaction_type": "WITHDRAWAL",
            "card_number": self.card_number,
            "pin": self.pin,
            "amount": withdrawal_amount,
            "atm_id": "ATM001",
            "db_session": self.db_session
        }
        
        withdrawal_result = process_atm_transaction(withdrawal_data)
        
        # Verify withdrawal successful
        self.assertTrue(withdrawal_result["success"])
        self.assertEqual(withdrawal_result["amount"], withdrawal_amount)
        
        # Verify account balance updated
        balance_data = {
            "transaction_type": "BALANCE_INQUIRY",
            "card_number": self.card_number,
            "pin": self.pin,
            "atm_id": "ATM001",
            "db_session": self.db_session
        }
        
        balance_result = process_atm_transaction(balance_data)
        
        # Expected balance is 20000 - 5000 = 15000
        self.assertEqual(balance_result["balance"], 15000.00)
        
        # Verify transaction was recorded
        transaction = self.db_session.query(Transaction).filter_by(
            account_id="E2E_ATM_ACC",
            transaction_type="ATM_WITHDRAWAL",
            amount=withdrawal_amount
        ).first()
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, "COMPLETED")
    
    def test_03_atm_pin_change(self):
        """Test ATM PIN change."""
        # Process PIN change
        new_pin = "5678"
        pin_change_data = {
            "transaction_type": "PIN_CHANGE",
            "card_number": self.card_number,
            "old_pin": self.pin,
            "new_pin": new_pin,
            "atm_id": "ATM001",
            "db_session": self.db_session
        }
        
        pin_result = process_atm_transaction(pin_change_data)
        
        # Verify PIN change successful
        self.assertTrue(pin_result["success"])
        
        # Try a transaction with the new PIN
        balance_data = {
            "transaction_type": "BALANCE_INQUIRY",
            "card_number": self.card_number,
            "pin": new_pin,  # Use new PIN
            "atm_id": "ATM001",
            "db_session": self.db_session
        }
        
        balance_result = process_atm_transaction(balance_data)
        
        # Verify transaction successful with new PIN
        self.assertTrue(balance_result["success"])
        
        # Try with old PIN (should fail)
        balance_data_old_pin = {
            "transaction_type": "BALANCE_INQUIRY",
            "card_number": self.card_number,
            "pin": self.pin,  # Old PIN
            "atm_id": "ATM001",
            "db_session": self.db_session
        }
        
        balance_result_old_pin = process_atm_transaction(balance_data_old_pin)
        
        # Verify transaction fails with old PIN
        self.assertFalse(balance_result_old_pin["success"])
        self.assertEqual(balance_result_old_pin["error"], "Invalid PIN")


if __name__ == "__main__":
    unittest.main()
