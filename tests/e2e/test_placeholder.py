"""
Core Banking System - End-to-End Customer Account Workflow Tests

This module contains end-to-end tests for a complete customer and account lifecycle.
These tests verify that all components work together in real-world scenarios.
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

# Import module interfaces and registry
from utils.lib.module_interface import ModuleRegistry

# Base URL for API
API_BASE_URL = "http://localhost:5000/api/v1"


@pytest.mark.skipif(
    os.environ.get("SKIP_E2E_TESTS") == "1",
    reason="E2E tests are disabled"
)
class TestCustomerAccountWorkflow(unittest.TestCase):
    """End-to-end tests for customer account workflows."""
    
    def setUp(self):
        """Set up test environment."""
        # Check if API is available
        try:
            response = requests.get(f"{API_BASE_URL}/health")
            if response.status_code != 200:
                self.skipTest("API server is not available")
        except requests.RequestException:
            self.skipTest("API server is not available")
        
        # Create test customer data
        self.customer_data = {
            "customer_id": "CUS_E2E_TEST",
            "first_name": "E2E",
            "last_name": "Test",
            "email": "e2e.test@example.com",
            "phone": "1234567890",
            "address": "123 E2E St, Test City",
            "date_of_birth": "1990-01-01"
        }
        
        # Create test account data
        self.account_data = {
            "account_id": "ACC_E2E_TEST",
            "customer_id": "CUS_E2E_TEST",
            "account_type": "SAVINGS",
            "currency": "USD",
            "initial_balance": 1000.00
        }
        
        # Clean up any existing test data
        self.cleanup_test_data()
    
    def tearDown(self):
        """Clean up after each test."""
        self.cleanup_test_data()
    
    def cleanup_test_data(self):
        """Clean up test data after tests."""
        try:
            # Close account if it exists
            requests.post(
                f"{API_BASE_URL}/accounts/{self.account_data['account_id']}/close",
                json={"reason": "E2E Test Cleanup"}
            )
            
            # Delete customer if it exists
            requests.delete(f"{API_BASE_URL}/customers/{self.customer_data['customer_id']}")
        except:
            # Ignore errors during cleanup
            pass
    
    def test_full_customer_account_workflow(self):
        """Test a complete customer and account lifecycle."""
        # 1. Create a customer
        customer_response = requests.post(
            f"{API_BASE_URL}/customers",
            json=self.customer_data
        )
        self.assertEqual(customer_response.status_code, 201)
        customer = customer_response.json()
        self.assertEqual(customer["customer_id"], self.customer_data["customer_id"])
        
        # 2. Create an account for the customer
        account_response = requests.post(
            f"{API_BASE_URL}/accounts",
            json=self.account_data
        )
        self.assertEqual(account_response.status_code, 201)
        account = account_response.json()
        self.assertEqual(account["account_id"], self.account_data["account_id"])
        self.assertEqual(float(account["balance"]), self.account_data["initial_balance"])
        
        # 3. Deposit funds into the account
        deposit_data = {
            "amount": 500.00,
            "currency": "USD",
            "description": "E2E Test Deposit"
        }
        deposit_response = requests.post(
            f"{API_BASE_URL}/accounts/{self.account_data['account_id']}/deposit",
            json=deposit_data
        )
        self.assertEqual(deposit_response.status_code, 200)
        
        # 4. Check updated balance
        balance_response = requests.get(
            f"{API_BASE_URL}/accounts/{self.account_data['account_id']}/balance"
        )
        self.assertEqual(balance_response.status_code, 200)
        balance_data = balance_response.json()
        self.assertEqual(float(balance_data["balance"]), 1500.00)
        
        # 5. Withdraw funds from the account
        withdraw_data = {
            "amount": 200.00,
            "currency": "USD",
            "description": "E2E Test Withdrawal"
        }
        withdraw_response = requests.post(
            f"{API_BASE_URL}/accounts/{self.account_data['account_id']}/withdraw",
            json=withdraw_data
        )
        self.assertEqual(withdraw_response.status_code, 200)
        
        # 6. Check transaction history
        history_response = requests.get(
            f"{API_BASE_URL}/accounts/{self.account_data['account_id']}/transactions"
        )
        self.assertEqual(history_response.status_code, 200)
        transactions = history_response.json()
        self.assertEqual(len(transactions), 2)  # 1 deposit + 1 withdrawal
        
        # 7. Close the account
        close_response = requests.post(
            f"{API_BASE_URL}/accounts/{self.account_data['account_id']}/close",
            json={"reason": "E2E Test Complete"}
        )
        self.assertEqual(close_response.status_code, 200)
        
        # 8. Verify account is closed
        account_response = requests.get(
            f"{API_BASE_URL}/accounts/{self.account_data['account_id']}"
        )
        self.assertEqual(account_response.status_code, 200)
        account = account_response.json()
        self.assertEqual(account["status"], "CLOSED")


# You can run this test file directly
if __name__ == "__main__":
    unittest.main()
