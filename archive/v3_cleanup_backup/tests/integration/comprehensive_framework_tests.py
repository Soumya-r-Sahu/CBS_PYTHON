import unittest
import requests
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Add project root to path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

# Import configuration
try:
    from Backend.utils.config.compatibility import (
        get_api_config,
        get_cors_settings,
        get_api_client_config,
        is_production,
        is_development
    )
except ImportError:
    # Fallback definitions if imports fail
    def get_api_config():
        return {
            "host": "localhost",
            "port": 5000,
            "allowed_origins": ["*"]
        }
    
    def get_cors_settings():
        return {
            "allowed_origins": ["*"],
            "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allowed_headers": ["Authorization", "Content-Type"],
            "expose_headers": [],
            "supports_credentials": True,
            "max_age": 3600
        }
    
    def get_api_client_config(framework="django"):
        return {
            "base_url": "http://localhost:5000/api/v1"
        }
    
    def is_production():
        return False
    
    def is_development():
        return True

class BaseAPICompatibilityTest(unittest.TestCase):
    """Base class for all API compatibility tests"""
    
    def setUp(self):
        """Setup test environment"""
        self.api_config = get_api_config()
        self.cors_settings = get_cors_settings()
        self.client_config = get_api_client_config(self.framework)
        
        # API base URL
        self.api_url = f"http://{self.api_config['host']}:{self.api_config['port']}/api/v1"
        
        # Create a session for requests
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"CBS-Python/CompatibilityTest-{self.framework}"
        })
        
        # Test data
        self.test_user = {
            "username": "test_user",
            "password": "Test@123",
            "email": "test@example.com"
        }
        
        self.test_account = {
            "account_type": "SAVINGS",
            "initial_deposit": 1000.00
        }
        
        self.test_transfer = {
            "from_account_id": None,  # Will be set during tests
            "to_account_id": None,    # Will be set during tests
            "amount": 100.00,
            "description": "Test transfer"
        }
        
        # Authentication token
        self.auth_token = None
    
    def authenticate(self):
        """Authenticate and get token"""
        auth_url = f"{self.api_url}/auth/login"
        response = self.session.post(
            auth_url,
            json={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("token")
            self.session.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })
            return True
        
        return False
    
    def test_cors_headers(self):
        """Test that CORS headers are properly set"""
        # Make an OPTIONS request to check CORS headers
        options_url = f"{self.api_url}/health"
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = self.session.options(options_url, headers=headers)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify Access-Control-Allow-Origin header
        self.assertIn("Access-Control-Allow-Origin", response.headers)
        allowed_origin = response.headers["Access-Control-Allow-Origin"]
        self.assertTrue(
            allowed_origin == "*" or allowed_origin == "http://localhost:3000",
            f"Expected CORS origin header to be * or http://localhost:3000, got {allowed_origin}"
        )
        
        # Verify Access-Control-Allow-Methods header
        self.assertIn("Access-Control-Allow-Methods", response.headers)
        allowed_methods = response.headers["Access-Control-Allow-Methods"]
        for method in ["GET", "POST", "PUT", "DELETE"]:
            self.assertIn(
                method, allowed_methods,
                f"Expected {method} to be in allowed methods, got {allowed_methods}"
            )
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        health_url = f"{self.api_url}/health"
        response = self.session.get(health_url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("status", data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("version", data)
        self.assertIn("service", data)

class DjangoCompatibilityTest(BaseAPICompatibilityTest):
    """Test API compatibility with Django frontend"""
    
    def __init__(self, *args, **kwargs):
        self.framework = "django"
        super().__init__(*args, **kwargs)
    
    def test_django_authentication_flow(self):
        """Test authentication flow with Django client"""
        # Login
        auth_url = f"{self.api_url}/auth/login"
        response = self.session.post(
            auth_url,
            json={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("token", data)
        self.auth_token = data["token"]
        
        # Update session with token
        self.session.headers.update({
            "Authorization": f"Bearer {self.auth_token}"
        })
        
        # Get user profile
        profile_url = f"{self.api_url}/customers/profile"
        response = self.session.get(profile_url)
        
        self.assertEqual(response.status_code, 200)
        profile_data = response.json()
        
        self.assertIn("id", profile_data)
        self.assertIn("username", profile_data)
        
        # Logout
        logout_url = f"{self.api_url}/auth/logout"
        response = self.session.post(logout_url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_django_account_operations(self):
        """Test account operations with Django client"""
        # Authenticate first
        self.authenticate()
        
        # Create account
        create_url = f"{self.api_url}/accounts"
        response = self.session.post(
            create_url,
            json=self.test_account
        )
        
        self.assertEqual(response.status_code, 201)
        account_data = response.json()
        
        self.assertIn("id", account_data)
        self.assertIn("account_number", account_data)
        self.assertIn("balance", account_data)
        
        account_id = account_data["id"]
        
        # Get account details
        details_url = f"{self.api_url}/accounts/{account_id}"
        response = self.session.get(details_url)
        
        self.assertEqual(response.status_code, 200)
        account_details = response.json()
        
        self.assertEqual(account_details["id"], account_id)
        self.assertEqual(account_details["account_type"], self.test_account["account_type"])
        
        # Get all accounts
        accounts_url = f"{self.api_url}/accounts"
        response = self.session.get(accounts_url)
        
        self.assertEqual(response.status_code, 200)
        accounts_list = response.json()
        
        self.assertTrue(isinstance(accounts_list, list))
        self.assertGreaterEqual(len(accounts_list), 1)
        
        # Clean up - delete test account
        delete_url = f"{self.api_url}/accounts/{account_id}"
        response = self.session.delete(delete_url)
        
        self.assertEqual(response.status_code, 204)

class ReactCompatibilityTest(BaseAPICompatibilityTest):
    """Test API compatibility with React frontend"""
    
    def __init__(self, *args, **kwargs):
        self.framework = "react"
        super().__init__(*args, **kwargs)
    
    def test_react_authentication_flow(self):
        """Test authentication flow with React client"""
        # Login
        auth_url = f"{self.api_url}/auth/login"
        response = self.session.post(
            auth_url,
            json={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("token", data)
        self.auth_token = data["token"]
        
        # Update session with token
        self.session.headers.update({
            "Authorization": f"Bearer {self.auth_token}"
        })
        
        # Get user profile
        profile_url = f"{self.api_url}/customers/profile"
        response = self.session.get(profile_url)
        
        self.assertEqual(response.status_code, 200)
        profile_data = response.json()
        
        self.assertIn("id", profile_data)
        self.assertIn("username", profile_data)
        
        # Verify token 
        verify_url = f"{self.api_url}/auth/verify"
        response = self.session.post(verify_url)
        
        self.assertEqual(response.status_code, 200)
        
        # Logout
        logout_url = f"{self.api_url}/auth/logout"
        response = self.session.post(logout_url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_react_transaction_operations(self):
        """Test transaction operations with React client"""
        # Authenticate first
        self.authenticate()
        
        # Create two accounts for testing transfers
        create_url = f"{self.api_url}/accounts"
        
        # Create source account
        response = self.session.post(
            create_url,
            json=self.test_account
        )
        
        self.assertEqual(response.status_code, 201)
        source_account = response.json()
        source_account_id = source_account["id"]
        
        # Create destination account
        response = self.session.post(
            create_url,
            json=self.test_account
        )
        
        self.assertEqual(response.status_code, 201)
        dest_account = response.json()
        dest_account_id = dest_account["id"]
        
        # Update test transfer data
        self.test_transfer["from_account_id"] = source_account_id
        self.test_transfer["to_account_id"] = dest_account_id
        
        # Create a transaction (transfer)
        transfer_url = f"{self.api_url}/transactions"
        response = self.session.post(
            transfer_url,
            json=self.test_transfer
        )
        
        self.assertEqual(response.status_code, 201)
        transfer_data = response.json()
        
        self.assertIn("id", transfer_data)
        self.assertIn("status", transfer_data)
        self.assertEqual(transfer_data["amount"], self.test_transfer["amount"])
        
        transaction_id = transfer_data["id"]
        
        # Get transaction details
        details_url = f"{self.api_url}/transactions/{transaction_id}"
        response = self.session.get(details_url)
        
        self.assertEqual(response.status_code, 200)
        transaction_details = response.json()
        
        self.assertEqual(transaction_details["id"], transaction_id)
        
        # Get account transactions
        account_transactions_url = f"{self.api_url}/accounts/{source_account_id}/transactions"
        response = self.session.get(account_transactions_url)
        
        self.assertEqual(response.status_code, 200)
        transactions_list = response.json()
        
        self.assertTrue(isinstance(transactions_list, list))
        self.assertGreaterEqual(len(transactions_list), 1)
        
        # Clean up - delete test accounts
        self.session.delete(f"{self.api_url}/accounts/{source_account_id}")
        self.session.delete(f"{self.api_url}/accounts/{dest_account_id}")

class AngularCompatibilityTest(BaseAPICompatibilityTest):
    """Test API compatibility with Angular frontend"""
    
    def __init__(self, *args, **kwargs):
        self.framework = "angular"
        super().__init__(*args, **kwargs)
    
    def test_angular_authentication_flow(self):
        """Test authentication flow with Angular client"""
        # Login with extended headers typical of Angular HttpClient
        auth_url = f"{self.api_url}/auth/login"
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json"
        }
        
        response = self.session.post(
            auth_url,
            headers=headers,
            json={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("token", data)
        self.auth_token = data["token"]
        
        # Update session with token in Authorization header
        self.session.headers.update({
            "Authorization": f"Bearer {self.auth_token}"
        })
        
        # Get user profile with Angular-typical headers
        profile_url = f"{self.api_url}/customers/profile"
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json"
        }
        
        response = self.session.get(profile_url, headers=headers)
        
        self.assertEqual(response.status_code, 200)
        profile_data = response.json()
        
        self.assertIn("id", profile_data)
        self.assertIn("username", profile_data)
        
        # Logout
        logout_url = f"{self.api_url}/auth/logout"
        response = self.session.post(logout_url, headers=headers)
        
        self.assertEqual(response.status_code, 200)
    
    def test_angular_card_operations(self):
        """Test card operations with Angular client"""
        # Authenticate first
        self.authenticate()
        
        # Create account for card
        create_account_url = f"{self.api_url}/accounts"
        response = self.session.post(
            create_account_url,
            json=self.test_account
        )
        
        self.assertEqual(response.status_code, 201)
        account_data = response.json()
        account_id = account_data["id"]
        
        # Create a card
        create_card_url = f"{self.api_url}/cards"
        card_data = {
            "account_id": account_id,
            "card_type": "DEBIT",
            "card_network": "VISA"
        }
        
        response = self.session.post(
            create_card_url,
            json=card_data
        )
        
        self.assertEqual(response.status_code, 201)
        card_response = response.json()
        
        self.assertIn("id", card_response)
        self.assertIn("card_number", card_response)
        self.assertEqual(card_response["status"], "ACTIVE")
        
        card_id = card_response["id"]
        
        # Get card details
        card_details_url = f"{self.api_url}/cards/{card_id}"
        response = self.session.get(card_details_url)
        
        self.assertEqual(response.status_code, 200)
        card_details = response.json()
        
        self.assertEqual(card_details["id"], card_id)
        
        # Update card status
        update_url = f"{self.api_url}/cards/{card_id}/status"
        update_data = {
            "status": "BLOCKED"
        }
        
        response = self.session.put(
            update_url,
            json=update_data
        )
        
        self.assertEqual(response.status_code, 200)
        updated_card = response.json()
        
        self.assertEqual(updated_card["status"], "BLOCKED")
        
        # Get all cards
        cards_url = f"{self.api_url}/cards"
        response = self.session.get(cards_url)
        
        self.assertEqual(response.status_code, 200)
        cards_list = response.json()
        
        self.assertTrue(isinstance(cards_list, list))
        self.assertGreaterEqual(len(cards_list), 1)
        
        # Clean up - delete test card and account
        self.session.delete(f"{self.api_url}/cards/{card_id}")
        self.session.delete(f"{self.api_url}/accounts/{account_id}")

class VueCompatibilityTest(BaseAPICompatibilityTest):
    """Test API compatibility with Vue.js frontend"""
    
    def __init__(self, *args, **kwargs):
        self.framework = "vue"
        super().__init__(*args, **kwargs)
    
    def test_vue_authentication_flow(self):
        """Test authentication flow with Vue client"""
        # Login
        auth_url = f"{self.api_url}/auth/login"
        response = self.session.post(
            auth_url,
            json={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("token", data)
        self.auth_token = data["token"]
        
        # Update session with token
        self.session.headers.update({
            "Authorization": f"Bearer {self.auth_token}"
        })
        
        # Get user profile
        profile_url = f"{self.api_url}/customers/profile"
        response = self.session.get(profile_url)
        
        self.assertEqual(response.status_code, 200)
        profile_data = response.json()
        
        self.assertIn("id", profile_data)
        self.assertIn("username", profile_data)
        
        # Logout
        logout_url = f"{self.api_url}/auth/logout"
        response = self.session.post(logout_url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_vue_upi_operations(self):
        """Test UPI operations with Vue client"""
        # Authenticate first
        self.authenticate()
        
        # Create account for UPI
        create_account_url = f"{self.api_url}/accounts"
        response = self.session.post(
            create_account_url,
            json=self.test_account
        )
        
        self.assertEqual(response.status_code, 201)
        account_data = response.json()
        account_id = account_data["id"]
        
        # Create UPI ID
        create_upi_url = f"{self.api_url}/upi/id"
        upi_data = {
            "account_id": account_id,
            "upi_id": f"test{int(time.time())}@cbs"
        }
        
        response = self.session.post(
            create_upi_url,
            json=upi_data
        )
        
        self.assertEqual(response.status_code, 201)
        upi_response = response.json()
        
        self.assertIn("id", upi_response)
        self.assertIn("upi_id", upi_response)
        self.assertEqual(upi_response["status"], "ACTIVE")
        
        upi_id = upi_response["id"]
        
        # Get UPI details
        upi_details_url = f"{self.api_url}/upi/id/{upi_id}"
        response = self.session.get(upi_details_url)
        
        self.assertEqual(response.status_code, 200)
        upi_details = response.json()
        
        self.assertEqual(upi_details["id"], upi_id)
        
        # Get all UPI IDs
        upi_list_url = f"{self.api_url}/upi/ids"
        response = self.session.get(upi_list_url)
        
        self.assertEqual(response.status_code, 200)
        upi_list = response.json()
        
        self.assertTrue(isinstance(upi_list, list))
        self.assertGreaterEqual(len(upi_list), 1)
        
        # Clean up - delete test UPI ID and account
        delete_upi_url = f"{self.api_url}/upi/id/{upi_id}"
        self.session.delete(delete_upi_url)
        self.session.delete(f"{self.api_url}/accounts/{account_id}")

if __name__ == "__main__":
    unittest.main()
