"""
Core Banking Payments End-to-End Tests

This module contains end-to-end tests for payment workflows.
These tests verify complete payment business processes from start to finish.
"""

import pytest
import unittest
import requests
import json
import sys
import os
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Base URL for API
API_BASE_URL = "http://localhost:5000/api/v1"


@pytest.mark.skipif(
    os.environ.get("SKIP_E2E_TESTS") == "1",
    reason="E2E tests are disabled"
)
class TestPaymentWorkflows(unittest.TestCase):
    """End-to-end tests for payment workflows."""
    
    def setUp(self):
        """Set up before each test."""
        # Create test customers
        self.customer1 = {
            "customer_id": "CUS_PAY_E2E_1",
            "first_name": "Payment",
            "last_name": "Sender",
            "email": "payment.sender@example.com"
        }
        
        self.customer2 = {
            "customer_id": "CUS_PAY_E2E_2",
            "first_name": "Payment",
            "last_name": "Receiver",
            "email": "payment.receiver@example.com"
        }
        
        # Create customers
        requests.post(f"{API_BASE_URL}/customers", json=self.customer1)
        requests.post(f"{API_BASE_URL}/customers", json=self.customer2)
        
        # Create accounts
        self.account1 = {
            "account_id": "ACC_PAY_E2E_1",
            "customer_id": "CUS_PAY_E2E_1",
            "account_type": "SAVINGS",
            "balance": 10000.00,
            "currency": "USD",
            "status": "ACTIVE"
        }
        
        self.account2 = {
            "account_id": "ACC_PAY_E2E_2",
            "customer_id": "CUS_PAY_E2E_2",
            "account_type": "SAVINGS",
            "balance": 5000.00,
            "currency": "USD",
            "status": "ACTIVE"
        }
        
        # Create accounts
        requests.post(f"{API_BASE_URL}/accounts", json=self.account1)
        requests.post(f"{API_BASE_URL}/accounts", json=self.account2)
        
        # Set up UPI IDs for the accounts
        requests.put(
            f"{API_BASE_URL}/accounts/{self.account1['account_id']}/upi",
            json={"upi_id": "sender@upi"}
        )
        
        requests.put(
            f"{API_BASE_URL}/accounts/{self.account2['account_id']}/upi",
            json={"upi_id": "receiver@upi"}
        )
    
    def tearDown(self):
        """Clean up after each test."""
        # Delete accounts
        requests.delete(f"{API_BASE_URL}/accounts/{self.account1['account_id']}")
        requests.delete(f"{API_BASE_URL}/accounts/{self.account2['account_id']}")
        
        # Delete customers
        requests.delete(f"{API_BASE_URL}/customers/{self.customer1['customer_id']}")
        requests.delete(f"{API_BASE_URL}/customers/{self.customer2['customer_id']}")
    
    def test_fund_transfer_neft_workflow(self):
        """Test the complete NEFT fund transfer workflow."""
        # Initial balances
        account1_initial_balance = self.account1["balance"]
        account2_initial_balance = self.account2["balance"]
        
        # Step 1: Create a NEFT transfer
        transfer_amount = 1000.00
        neft_transfer = {
            "source_account_id": self.account1["account_id"],
            "destination_account_id": self.account2["account_id"],
            "destination_ifsc": "HDFC0001234",
            "amount": transfer_amount,
            "currency": "USD",
            "description": "E2E Test NEFT Transfer",
            "payment_mode": "NEFT"
        }
        
        response = requests.post(f"{API_BASE_URL}/payments/transfers", json=neft_transfer)
        self.assertEqual(response.status_code, 201)
        
        # Get transfer ID
        transfer_data = response.json()
        transfer_id = transfer_data["transfer_id"]
        
        # Step 2: Check transfer status
        response = requests.get(f"{API_BASE_URL}/payments/transfers/{transfer_id}")
        self.assertEqual(response.status_code, 200)
        transfer = response.json()
        
        # Initially may be pending
        if transfer["status"] == "PENDING":
            # Wait for processing to complete
            max_retries = 5
            for i in range(max_retries):
                time.sleep(1)  # Wait for 1 second
                response = requests.get(f"{API_BASE_URL}/payments/transfers/{transfer_id}")
                transfer = response.json()
                if transfer["status"] != "PENDING":
                    break
        
        # Verify transfer was completed
        self.assertEqual(transfer["status"], "COMPLETED")
        
        # Step 3: Check source account balance
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account1['account_id']}")
        self.assertEqual(response.status_code, 200)
        source_account = response.json()
        
        # Verify balance was reduced
        self.assertEqual(source_account["balance"], account1_initial_balance - transfer_amount)
        
        # Step 4: Check destination account balance
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account2['account_id']}")
        self.assertEqual(response.status_code, 200)
        destination_account = response.json()
        
        # Verify balance was increased
        self.assertEqual(destination_account["balance"], account2_initial_balance + transfer_amount)
        
        # Step 5: Check transaction history for source account
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account1['account_id']}/transactions")
        self.assertEqual(response.status_code, 200)
        source_transactions = response.json()
        
        # Find the transfer transaction
        source_transfer = None
        for transaction in source_transactions:
            if transaction["amount"] == transfer_amount and "NEFT" in transaction["transaction_type"]:
                source_transfer = transaction
                break
        
        # Verify source transaction
        self.assertIsNotNone(source_transfer)
        self.assertEqual(source_transfer["status"], "COMPLETED")
        
        # Step 6: Check transaction history for destination account
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account2['account_id']}/transactions")
        self.assertEqual(response.status_code, 200)
        destination_transactions = response.json()
        
        # Find the transfer transaction
        destination_transfer = None
        for transaction in destination_transactions:
            if transaction["amount"] == transfer_amount and "NEFT" in transaction["transaction_type"]:
                destination_transfer = transaction
                break
        
        # Verify destination transaction
        self.assertIsNotNone(destination_transfer)
        self.assertEqual(destination_transfer["status"], "COMPLETED")
    
    def test_upi_payment_workflow(self):
        """Test the complete UPI payment workflow."""
        # Initial balances
        account1_initial_balance = self.account1["balance"]
        account2_initial_balance = self.account2["balance"]
        
        # Step 1: Create a UPI payment
        payment_amount = 500.00
        upi_payment = {
            "source_vpa": "sender@upi",
            "destination_vpa": "receiver@upi",
            "amount": payment_amount,
            "currency": "USD",
            "description": "E2E Test UPI Payment",
            "reference_id": "UPI" + str(int(time.time()))
        }
        
        response = requests.post(f"{API_BASE_URL}/payments/upi", json=upi_payment)
        self.assertEqual(response.status_code, 201)
        
        # Get payment ID
        payment_data = response.json()
        payment_id = payment_data["payment_id"]
        
        # Step 2: Check payment status
        response = requests.get(f"{API_BASE_URL}/payments/upi/{payment_id}")
        self.assertEqual(response.status_code, 200)
        payment = response.json()
        
        # Wait for processing to complete if needed
        if payment["status"] == "PENDING":
            max_retries = 5
            for i in range(max_retries):
                time.sleep(1)  # Wait for 1 second
                response = requests.get(f"{API_BASE_URL}/payments/upi/{payment_id}")
                payment = response.json()
                if payment["status"] != "PENDING":
                    break
        
        # Verify payment was completed
        self.assertEqual(payment["status"], "COMPLETED")
        
        # Step 3: Check source account balance
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account1['account_id']}")
        self.assertEqual(response.status_code, 200)
        source_account = response.json()
        
        # Verify balance was reduced
        self.assertEqual(source_account["balance"], account1_initial_balance - payment_amount)
        
        # Step 4: Check destination account balance
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account2['account_id']}")
        self.assertEqual(response.status_code, 200)
        destination_account = response.json()
        
        # Verify balance was increased
        self.assertEqual(destination_account["balance"], account2_initial_balance + payment_amount)
        
        # Step 5: Get UPI payment history for source account
        response = requests.get(f"{API_BASE_URL}/payments/upi?source_vpa=sender@upi")
        self.assertEqual(response.status_code, 200)
        sent_payments = response.json()
        
        # Verify payment is in history
        self.assertGreaterEqual(len(sent_payments), 1)
        found_payment = False
        for p in sent_payments:
            if p["payment_id"] == payment_id:
                found_payment = True
                break
        
        self.assertTrue(found_payment)


@pytest.mark.skipif(
    os.environ.get("SKIP_E2E_TESTS") == "1",
    reason="E2E tests are disabled"
)
class TestBillPaymentWorkflow(unittest.TestCase):
    """End-to-end tests for bill payment workflow."""
    
    def setUp(self):
        """Set up before each test."""
        # Create test customer
        self.customer = {
            "customer_id": "CUS_BILL_E2E",
            "first_name": "Bill",
            "last_name": "Payer",
            "email": "bill.payer@example.com"
        }
        
        # Create customer
        requests.post(f"{API_BASE_URL}/customers", json=self.customer)
        
        # Create account
        self.account = {
            "account_id": "ACC_BILL_E2E",
            "customer_id": "CUS_BILL_E2E",
            "account_type": "SAVINGS",
            "balance": 10000.00,
            "currency": "USD",
            "status": "ACTIVE"
        }
        
        # Create account
        requests.post(f"{API_BASE_URL}/accounts", json=self.account)
    
    def tearDown(self):
        """Clean up after each test."""
        # Delete account
        requests.delete(f"{API_BASE_URL}/accounts/{self.account['account_id']}")
        
        # Delete customer
        requests.delete(f"{API_BASE_URL}/customers/{self.customer['customer_id']}")
    
    def test_utility_bill_payment_workflow(self):
        """Test the complete utility bill payment workflow."""
        # Initial balance
        account_initial_balance = self.account["balance"]
        
        # Step 1: Get list of billers
        response = requests.get(f"{API_BASE_URL}/payments/billers?category=ELECTRICITY")
        self.assertEqual(response.status_code, 200)
        billers = response.json()
        
        # Pick the first biller
        self.assertGreaterEqual(len(billers), 1)
        biller = billers[0]
        
        # Step 2: Validate consumer number
        consumer_number = "123456789"
        validation = {
            "biller_id": biller["biller_id"],
            "consumer_number": consumer_number
        }
        
        response = requests.post(f"{API_BASE_URL}/payments/billers/validate", json=validation)
        self.assertEqual(response.status_code, 200)
        validation_result = response.json()
        
        # Verify validation succeeded
        self.assertTrue(validation_result["valid"])
        self.assertIn("customer_name", validation_result)
        
        # Step 3: Fetch bill details
        bill_fetch = {
            "biller_id": biller["biller_id"],
            "consumer_number": consumer_number
        }
        
        response = requests.post(f"{API_BASE_URL}/payments/billers/fetch-bill", json=bill_fetch)
        self.assertEqual(response.status_code, 200)
        bill = response.json()
        
        # Verify bill details
        self.assertIn("bill_number", bill)
        self.assertIn("amount", bill)
        self.assertIn("due_date", bill)
        
        # Step 4: Pay the bill
        bill_payment = {
            "account_id": self.account["account_id"],
            "biller_id": biller["biller_id"],
            "consumer_number": consumer_number,
            "bill_number": bill["bill_number"],
            "amount": bill["amount"],
            "payment_date": "2023-01-01",
            "remarks": "E2E Test Bill Payment"
        }
        
        response = requests.post(f"{API_BASE_URL}/payments/bills", json=bill_payment)
        self.assertEqual(response.status_code, 201)
        
        # Get payment ID
        payment_data = response.json()
        payment_id = payment_data["payment_id"]
        
        # Step 5: Check payment status
        response = requests.get(f"{API_BASE_URL}/payments/bills/{payment_id}")
        self.assertEqual(response.status_code, 200)
        payment = response.json()
        
        # Wait for processing to complete if needed
        if payment["status"] == "PENDING":
            max_retries = 5
            for i in range(max_retries):
                time.sleep(1)  # Wait for 1 second
                response = requests.get(f"{API_BASE_URL}/payments/bills/{payment_id}")
                payment = response.json()
                if payment["status"] != "PENDING":
                    break
        
        # Verify payment was completed
        self.assertEqual(payment["status"], "COMPLETED")
        
        # Step 6: Check account balance
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account['account_id']}")
        self.assertEqual(response.status_code, 200)
        updated_account = response.json()
        
        # Verify balance was reduced
        self.assertEqual(updated_account["balance"], account_initial_balance - bill["amount"])
        
        # Step 7: Get bill payment history
        response = requests.get(f"{API_BASE_URL}/payments/bills?account_id={self.account['account_id']}")
        self.assertEqual(response.status_code, 200)
        bill_payments = response.json()
        
        # Verify payment is in history
        self.assertGreaterEqual(len(bill_payments), 1)
        found_payment = False
        for p in bill_payments:
            if p["payment_id"] == payment_id:
                found_payment = True
                break
        
        self.assertTrue(found_payment)
        
        # Step 8: Get payment receipt
        response = requests.get(f"{API_BASE_URL}/payments/bills/{payment_id}/receipt")
        self.assertEqual(response.status_code, 200)
        receipt = response.json()
        
        # Verify receipt contains expected fields
        self.assertIn("receipt_number", receipt)
        self.assertIn("payment_date", receipt)
        self.assertIn("biller_name", receipt)
        self.assertIn("consumer_number", receipt)
        self.assertIn("amount", receipt)


if __name__ == "__main__":
    unittest.main()
