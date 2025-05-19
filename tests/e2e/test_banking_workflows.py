"""
Core Banking End-to-End Tests

This module contains end-to-end tests for the Core Banking System.
These tests verify complete business workflows.
"""

import pytest
import unittest
import requests
import json
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import utilities
from Tests.e2e.db_workflow_utils import verify_transaction_flow

# Base URL for API
API_BASE_URL = "http://localhost:5000/api/v1"


@pytest.mark.skipif(
    os.environ.get("SKIP_E2E_TESTS") == "1",
    reason="E2E tests are disabled"
)
class TestAccountTransactionWorkflow(unittest.TestCase):
    """End-to-end tests for account transaction workflows."""
    
    def setUp(self):
        """Set up before each test."""
        # Create test customers
        self.customer1 = {
            "customer_id": "CUS_E2E_1",
            "first_name": "E2E",
            "last_name": "Test One",
            "email": "e2e.test1@example.com"
        }
        
        self.customer2 = {
            "customer_id": "CUS_E2E_2",
            "first_name": "E2E",
            "last_name": "Test Two",
            "email": "e2e.test2@example.com"
        }
        
        # Create customers
        requests.post(f"{API_BASE_URL}/customers", json=self.customer1)
        requests.post(f"{API_BASE_URL}/customers", json=self.customer2)
        
        # Create accounts
        self.account1 = {
            "account_id": "ACC_E2E_1",
            "customer_id": "CUS_E2E_1",
            "account_type": "SAVINGS",
            "balance": 1000.00,
            "currency": "USD",
            "status": "ACTIVE"
        }
        
        self.account2 = {
            "account_id": "ACC_E2E_2",
            "customer_id": "CUS_E2E_2",
            "account_type": "SAVINGS",
            "balance": 500.00,
            "currency": "USD",
            "status": "ACTIVE"
        }
        
        # Create accounts
        requests.post(f"{API_BASE_URL}/accounts", json=self.account1)
        requests.post(f"{API_BASE_URL}/accounts", json=self.account2)
    
    def tearDown(self):
        """Clean up after each test."""
        # Delete accounts
        requests.delete(f"{API_BASE_URL}/accounts/{self.account1['account_id']}")
        requests.delete(f"{API_BASE_URL}/accounts/{self.account2['account_id']}")
        
        # Delete customers
        requests.delete(f"{API_BASE_URL}/customers/{self.customer1['customer_id']}")
        requests.delete(f"{API_BASE_URL}/customers/{self.customer2['customer_id']}")
    
    def test_fund_transfer_workflow(self):
        """Test end-to-end fund transfer workflow."""
        # Initial balances
        account1_initial_balance = self.account1["balance"]
        account2_initial_balance = self.account2["balance"]
        
        # Create a fund transfer
        transfer_amount = 200.00
        transfer = {
            "transaction_id": "TRX_E2E_TRANSFER",
            "source_account_id": self.account1["account_id"],
            "destination_account_id": self.account2["account_id"],
            "amount": transfer_amount,
            "currency": "USD",
            "description": "E2E Test Transfer"
        }
        
        # Execute the transfer
        response = requests.post(f"{API_BASE_URL}/transactions/transfer", json=transfer)
        
        # Verify transfer was successful
        self.assertEqual(response.status_code, 201)
        
        # Check source account balance
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account1['account_id']}")
        source_account = response.json()
        self.assertEqual(source_account["balance"], account1_initial_balance - transfer_amount)
        
        # Check destination account balance
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account2['account_id']}")
        destination_account = response.json()
        self.assertEqual(destination_account["balance"], account2_initial_balance + transfer_amount)
        
        # Check transaction history for source account
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account1['account_id']}/transactions")
        source_transactions = response.json()
        self.assertGreaterEqual(len(source_transactions), 1)
        
        # Find the transfer transaction
        source_transfer = None
        for transaction in source_transactions:
            if transaction["transaction_id"] == transfer["transaction_id"]:
                source_transfer = transaction
                break
        
        # Verify source transaction
        self.assertIsNotNone(source_transfer)
        self.assertEqual(source_transfer["amount"], transfer_amount)
        self.assertEqual(source_transfer["transaction_type"], "TRANSFER_OUT")
        
        # Check transaction history for destination account
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account2['account_id']}/transactions")
        destination_transactions = response.json()
        self.assertGreaterEqual(len(destination_transactions), 1)
        
        # Find the transfer transaction
        destination_transfer = None
        for transaction in destination_transactions:
            if transaction["transaction_id"].startswith("TRX_E2E_TRANSFER"):
                destination_transfer = transaction
                break
        
        # Verify destination transaction
        self.assertIsNotNone(destination_transfer)
        self.assertEqual(destination_transfer["amount"], transfer_amount)
        self.assertEqual(destination_transfer["transaction_type"], "TRANSFER_IN")


@pytest.mark.skipif(
    os.environ.get("SKIP_E2E_TESTS") == "1",
    reason="E2E tests are disabled"
)
class TestCustomerOnboardingWorkflow(unittest.TestCase):
    """End-to-end tests for customer onboarding workflow."""
    
    def tearDown(self):
        """Clean up after each test."""
        # Delete any created resources
        if hasattr(self, "account_id"):
            requests.delete(f"{API_BASE_URL}/accounts/{self.account_id}")
        
        if hasattr(self, "customer_id"):
            requests.delete(f"{API_BASE_URL}/customers/{self.customer_id}")
    
    def test_customer_onboarding_workflow(self):
        """Test end-to-end customer onboarding workflow."""
        # Step 1: Create a customer
        customer_data = {
            "first_name": "New",
            "last_name": "Customer",
            "email": "new.customer@example.com",
            "phone": "1234567890",
            "address": "123 New St, Customer City",
            "date_of_birth": "1990-01-01"
        }
        
        response = requests.post(f"{API_BASE_URL}/customers", json=customer_data)
        self.assertEqual(response.status_code, 201)
        
        # Get the created customer ID
        created_customer = response.json()
        self.customer_id = created_customer["customer_id"]
        
        # Step 2: Verify customer was created
        response = requests.get(f"{API_BASE_URL}/customers/{self.customer_id}")
        self.assertEqual(response.status_code, 200)
        
        retrieved_customer = response.json()
        self.assertEqual(retrieved_customer["first_name"], customer_data["first_name"])
        self.assertEqual(retrieved_customer["last_name"], customer_data["last_name"])
        self.assertEqual(retrieved_customer["email"], customer_data["email"])
        
        # Step 3: Create an account for the customer
        account_data = {
            "customer_id": self.customer_id,
            "account_type": "SAVINGS",
            "balance": 100.00,
            "currency": "USD"
        }
        
        response = requests.post(f"{API_BASE_URL}/accounts", json=account_data)
        self.assertEqual(response.status_code, 201)
        
        # Get the created account ID
        created_account = response.json()
        self.account_id = created_account["account_id"]
        
        # Step 4: Verify account was created
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account_id}")
        self.assertEqual(response.status_code, 200)
        
        retrieved_account = response.json()
        self.assertEqual(retrieved_account["customer_id"], self.customer_id)
        self.assertEqual(retrieved_account["account_type"], account_data["account_type"])
        self.assertEqual(retrieved_account["balance"], account_data["balance"])
        self.assertEqual(retrieved_account["status"], "ACTIVE")
        
        # Step 5: Verify customer has the account
        response = requests.get(f"{API_BASE_URL}/customers/{self.customer_id}/accounts")
        self.assertEqual(response.status_code, 200)
        
        customer_accounts = response.json()
        self.assertGreaterEqual(len(customer_accounts), 1)
        
        # Find our account in the list
        created_account = None
        for account in customer_accounts:
            if account["account_id"] == self.account_id:
                created_account = account
                break
        
        self.assertIsNotNone(created_account)
        self.assertEqual(created_account["account_type"], account_data["account_type"])
        
        # Step 6: Make an initial deposit
        deposit_data = {
            "transaction_id": "TRX_INITIAL_DEPOSIT",
            "account_id": self.account_id,
            "transaction_type": "DEPOSIT",
            "amount": 500.00,
            "currency": "USD",
            "description": "Initial deposit"
        }
        
        response = requests.post(f"{API_BASE_URL}/transactions", json=deposit_data)
        self.assertEqual(response.status_code, 201)
        
        # Step 7: Verify account balance was updated
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account_id}")
        self.assertEqual(response.status_code, 200)
        
        updated_account = response.json()
        self.assertEqual(updated_account["balance"], account_data["balance"] + deposit_data["amount"])


if __name__ == "__main__":
    unittest.main()
