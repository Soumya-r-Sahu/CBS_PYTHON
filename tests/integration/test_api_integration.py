"""
Core Banking API Integration Tests

This module contains integration tests for the API endpoints.
These tests require the API server to be running.
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

# Base URL for API
API_BASE_URL = "http://localhost:5000/api/v1"

@pytest.mark.skipif(
    os.environ.get("SKIP_API_TESTS") == "1",
    reason="API tests are disabled"
)
class TestCustomerAPI(unittest.TestCase):
    """Integration tests for Customer API endpoints."""
    
    def setUp(self):
        """Set up before each test."""
        # Create a test customer via API
        self.test_customer = {
            "customer_id": "CUS_API_TEST",
            "first_name": "API",
            "last_name": "Test",
            "email": "api.test@example.com",
            "phone": "1234567890",
            "address": "123 API St, Test City",
            "date_of_birth": "1990-01-01"
        }
        
        # Create the customer
        response = requests.post(
            f"{API_BASE_URL}/customers",
            json=self.test_customer
        )
        
        # Verify customer was created
        self.assertEqual(response.status_code, 201)
    
    def tearDown(self):
        """Clean up after each test."""
        # Delete the test customer
        requests.delete(f"{API_BASE_URL}/customers/{self.test_customer['customer_id']}")
    
    def test_get_customer(self):
        """Test retrieving a customer via API."""
        response = requests.get(
            f"{API_BASE_URL}/customers/{self.test_customer['customer_id']}"
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["customer_id"], self.test_customer["customer_id"])
        self.assertEqual(data["first_name"], self.test_customer["first_name"])
        self.assertEqual(data["last_name"], self.test_customer["last_name"])
        self.assertEqual(data["email"], self.test_customer["email"])
    
    def test_update_customer(self):
        """Test updating a customer via API."""
        # Updated customer data
        updated_data = {
            "email": "updated.api.test@example.com",
            "phone": "9876543210"
        }
        
        # Update the customer
        response = requests.put(
            f"{API_BASE_URL}/customers/{self.test_customer['customer_id']}",
            json=updated_data
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Get the updated customer
        response = requests.get(
            f"{API_BASE_URL}/customers/{self.test_customer['customer_id']}"
        )
        
        # Verify the customer was updated
        data = response.json()
        self.assertEqual(data["email"], updated_data["email"])
        self.assertEqual(data["phone"], updated_data["phone"])
    
    def test_list_customers(self):
        """Test listing customers via API."""
        response = requests.get(f"{API_BASE_URL}/customers")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        # Find our test customer in the list
        test_customer = None
        for customer in data:
            if customer["customer_id"] == self.test_customer["customer_id"]:
                test_customer = customer
                break
        
        # Verify our test customer is in the list
        self.assertIsNotNone(test_customer)
        self.assertEqual(test_customer["first_name"], self.test_customer["first_name"])
        self.assertEqual(test_customer["last_name"], self.test_customer["last_name"])


@pytest.mark.skipif(
    os.environ.get("SKIP_API_TESTS") == "1",
    reason="API tests are disabled"
)
class TestAccountAPI(unittest.TestCase):
    """Integration tests for Account API endpoints."""
    
    def setUp(self):
        """Set up before each test."""
        # Create a test customer
        self.test_customer = {
            "customer_id": "CUS_ACC_API_TEST",
            "first_name": "Account",
            "last_name": "API Test",
            "email": "account.api.test@example.com"
        }
        
        # Create the customer
        response = requests.post(
            f"{API_BASE_URL}/customers",
            json=self.test_customer
        )
        
        # Create a test account
        self.test_account = {
            "account_id": "ACC_API_TEST",
            "customer_id": "CUS_ACC_API_TEST",
            "account_type": "SAVINGS",
            "balance": 1000.00,
            "currency": "USD",
            "status": "ACTIVE"
        }
        
        # Create the account
        response = requests.post(
            f"{API_BASE_URL}/accounts",
            json=self.test_account
        )
        
        # Verify account was created
        self.assertEqual(response.status_code, 201)
    
    def tearDown(self):
        """Clean up after each test."""
        # Delete the test account
        requests.delete(f"{API_BASE_URL}/accounts/{self.test_account['account_id']}")
        
        # Delete the test customer
        requests.delete(f"{API_BASE_URL}/customers/{self.test_customer['customer_id']}")
    
    def test_get_account(self):
        """Test retrieving an account via API."""
        response = requests.get(
            f"{API_BASE_URL}/accounts/{self.test_account['account_id']}"
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["account_id"], self.test_account["account_id"])
        self.assertEqual(data["customer_id"], self.test_account["customer_id"])
        self.assertEqual(data["account_type"], self.test_account["account_type"])
        self.assertEqual(data["balance"], self.test_account["balance"])
    
    def test_update_account(self):
        """Test updating an account via API."""
        # Updated account data
        updated_data = {
            "balance": 1500.00,
            "status": "INACTIVE"
        }
        
        # Update the account
        response = requests.put(
            f"{API_BASE_URL}/accounts/{self.test_account['account_id']}",
            json=updated_data
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Get the updated account
        response = requests.get(
            f"{API_BASE_URL}/accounts/{self.test_account['account_id']}"
        )
        
        # Verify the account was updated
        data = response.json()
        self.assertEqual(data["balance"], updated_data["balance"])
        self.assertEqual(data["status"], updated_data["status"])
    
    def test_list_customer_accounts(self):
        """Test listing accounts for a customer via API."""
        response = requests.get(
            f"{API_BASE_URL}/customers/{self.test_customer['customer_id']}/accounts"
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        # Find our test account in the list
        test_account = None
        for account in data:
            if account["account_id"] == self.test_account["account_id"]:
                test_account = account
                break
        
        # Verify our test account is in the list
        self.assertIsNotNone(test_account)
        self.assertEqual(test_account["account_type"], self.test_account["account_type"])
        self.assertEqual(test_account["balance"], self.test_account["balance"])


if __name__ == "__main__":
    unittest.main()
