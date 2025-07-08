"""
Cross-Framework Compatibility Test Utility

This module provides tools for testing API compatibility with different frontend frameworks.
It can be used to verify that the Core Banking System API works correctly with various
frontend frameworks including Django, React, Angular, and Vue.js.
"""

import os
import sys
import unittest
import requests
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Add project root to path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

# Import configuration with fallback
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


class CompatibilityTester:
    """
    Tester utility for verifying cross-framework compatibility
    """
    
    def __init__(self, framework: str = None, api_url: str = None):
        """
        Initialize the compatibility tester
        
        Args:
            framework: Frontend framework to test (django, react, angular, vue)
            api_url: Optional override for API URL
        """
        self.framework = framework or "generic"
        self.client_config = get_api_client_config(self.framework)
        
        # Use provided URL or get from config
        if api_url:
            self.api_url = api_url
        else:
            self.api_url = self.client_config.get("base_url")
        
        # Prepare session for requests
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"CBS-Python/CompatibilityTest-{self.framework}"
        })
    
    def get_cors_headers(self) -> Dict[str, str]:
        """
        Get appropriate CORS headers for the selected framework
        
        Returns:
            Dictionary of CORS request headers
        """
        cors_config = get_cors_settings()
        
        headers = {}
        
        # Add framework-specific headers
        if self.framework == "django":
            headers["X-CSRFToken"] = "test-csrf-token"
            headers["X-Django-CSRF-Token"] = "test-csrf-token"
        elif self.framework in ["react", "nextjs"]:
            headers["X-Requested-With"] = "XMLHttpRequest"
        
        return headers
    
    def test_cors_preflight(self, endpoint: str = "health") -> Dict[str, Any]:
        """
        Test CORS preflight (OPTIONS) request
        
        Args:
            endpoint: API endpoint to test
            
        Returns:
            Dictionary with test results
        """
        url = f"{self.api_url}/{endpoint}"
        
        # Prepare CORS preflight headers
        cors_settings = get_cors_settings()
        
        headers = {
            "Origin": self._get_test_origin(),
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type, Authorization"
        }
        
        # Make OPTIONS request
        try:
            response = self.session.options(url, headers=headers)
            
            # Check for CORS headers in response
            cors_headers_present = (
                "Access-Control-Allow-Origin" in response.headers and
                "Access-Control-Allow-Methods" in response.headers
            )
            
            return {
                "success": cors_headers_present,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "message": "CORS preflight successful" if cors_headers_present else "CORS headers missing"
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "status_code": 0,
                "message": f"Request failed: {str(e)}"
            }
    
    def test_api_health(self) -> Dict[str, Any]:
        """
        Test API health endpoint with framework-specific headers
        
        Returns:
            Dictionary with test results
        """
        url = f"{self.api_url}/health"
        
        headers = {
            "Origin": self._get_test_origin(),
            **self.get_cors_headers()
        }
        
        try:
            response = self.session.get(url, headers=headers)
            
            return {
                "success": response.ok,
                "status_code": response.status_code,
                "data": response.json() if response.ok else None,
                "headers": dict(response.headers),
                "message": "Health check successful" if response.ok else f"Failed with status {response.status_code}"
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "status_code": 0,
                "message": f"Request failed: {str(e)}"
            }
    
    def _get_test_origin(self) -> str:
        """
        Get appropriate origin URL for the selected framework
        
        Returns:
            Origin URL string
        """
        if self.framework == "django":
            return "http://localhost:8000"
        elif self.framework in ["react", "nextjs"]:
            return "http://localhost:3000"
        elif self.framework == "angular":
            return "http://localhost:4200"
        elif self.framework == "vue":
            return "http://localhost:8080"
        else:
            return "http://localhost:9000"
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all compatibility tests
        
        Returns:
            Dictionary with test results
        """
        results = {
            "framework": self.framework,
            "api_url": self.api_url,
            "cors_preflight": self.test_cors_preflight(),
            "api_health": self.test_api_health()
        }
        
        # Calculate overall success
        results["success"] = all(
            results[test]["success"] 
            for test in ["cors_preflight", "api_health"]
        )
        
        return results


def test_all_frameworks(api_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Test compatibility with all supported frameworks
    
    Args:
        api_url: Optional override for API URL
        
    Returns:
        Dictionary with test results for all frameworks
    """
    frameworks = ["django", "react", "angular", "vue"]
    results = {}
    
    for framework in frameworks:
        tester = CompatibilityTester(framework, api_url)
        results[framework] = tester.run_all_tests()
    
    return results


if __name__ == "__main__":
    # When run directly, execute tests for all frameworks
    api_config = get_api_config()
    default_url = f"http://{api_config['host']}:{api_config['port']}/api/v1"
    
    # Allow command-line override of API URL
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    else:
        api_url = default_url
    
    print(f"Testing cross-framework compatibility with API at: {api_url}")
    
    # Run tests for all frameworks
    results = test_all_frameworks(api_url)
    
    # Print results
    print("\nTest Results:")
    print("=============")
    
    for framework, result in results.items():
        success = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{framework.upper()}: {success}")
        
        # Print details of failed tests
        if not result["success"]:
            for test_name, test_result in result.items():
                if isinstance(test_result, dict) and "success" in test_result and not test_result["success"]:
                    print(f"  - {test_name}: {test_result['message']}")
      # Save results to file
    output_file = os.path.join(project_root, "compatibility_test_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)


# Enhanced framework tests using Python's unittest framework
class BaseCrossPlatformTest(unittest.TestCase):
    """Base test case with common setup and utility methods for all framework tests"""
    
    def setUp(self):
        """Set up before each test"""
        api_config = get_api_config()
        default_url = f"http://{api_config['host']}:{api_config['port']}/api/v1"
        
        self.api_url = os.environ.get('CBS_TEST_API_URL', default_url)
        self.test_username = os.environ.get('CBS_TEST_USERNAME', 'testuser')
        self.test_password = os.environ.get('CBS_TEST_PASSWORD', 'Test@123')
        self.auth_token = None
        self.timeout = 10  # seconds
        
        # Test data
        self.test_account = None
        self.test_card = None
        
        # Setup test
        self._authenticate()
        self._setup_test_data()
    
    def tearDown(self):
        """Clean up after each test"""
        self._cleanup_test_data()
    
    def _authenticate(self):
        """Authenticate with the API and get token"""
        # This is implemented by each specific framework test class
        raise NotImplementedError("Authentication must be implemented by subclasses")
    
    def _setup_test_data(self):
        """Set up test data for use in tests"""
        # Get first account for tests
        self.test_account = self._get_first_account()
        # Get first card for tests
        self.test_card = self._get_first_card()
    
    def _cleanup_test_data(self):
        """Clean up any test data created during tests"""
        # Implemented by specific tests that create data
        pass
    
    def _get_first_account(self):
        """Get the first account for testing"""
        # This is implemented by each specific framework test class
        raise NotImplementedError("Get first account must be implemented by subclasses")
    
    def _get_first_card(self):
        """Get the first card for testing"""
        # This is implemented by each specific framework test class
        raise NotImplementedError("Get first card must be implemented by subclasses")


class DjangoClientTest(BaseCrossPlatformTest):
    """Test suite for Django client compatibility"""
    
    def _authenticate(self):
        """Authenticate using the Django client"""
        try:
            from Backend.integration_interfaces.django_client.django_api_client import BankingApiClient
            
            self.client = BankingApiClient(base_url=self.api_url)
            auth_result = self.client.authenticate(self.test_username, self.test_password)
            self.assertTrue(auth_result.success, "Django client authentication failed")
            self.auth_token = self.client.auth_token
        except ImportError:
            self.skipTest("Django client not available")
    
    def _get_first_account(self):
        """Get the first account using Django client"""
        accounts = self.client.get_accounts()
        self.assertTrue(len(accounts) > 0, "No accounts found for test user")
        return accounts[0]
    
    def _get_first_card(self):
        """Get the first card using Django client"""
        cards = self.client.get_cards()
        if len(cards) == 0:
            self.skipTest("No cards found for test user")
        return cards[0]
    
    def test_get_account_details(self):
        """Test retrieving account details using Django client"""
        account_id = self.test_account.get('id')
        account_details = self.client.get_account_details(account_id)
        self.assertEqual(account_details.get('id'), account_id)
        self.assertIsNotNone(account_details.get('accountNumber'))
    
    def test_get_account_transactions(self):
        """Test retrieving account transactions using Django client"""
        account_id = self.test_account.get('id')
        transactions = self.client.get_account_transactions(account_id)
        self.assertIsInstance(transactions, list)
    
    def test_get_account_balance(self):
        """Test retrieving account balance using Django client"""
        account_id = self.test_account.get('id')
        balance = self.client.get_account_balance(account_id)
        self.assertIsNotNone(balance.get('currentBalance'))
        self.assertIsNotNone(balance.get('availableBalance'))
    
    def test_get_customer_profile(self):
        """Test retrieving customer profile using Django client"""
        profile = self.client.get_customer_profile()
        self.assertIsNotNone(profile.get('id'))
        self.assertIsNotNone(profile.get('firstName'))
        self.assertIsNotNone(profile.get('lastName'))


class ReactClientTest(BaseCrossPlatformTest):
    """
    Test suite for React client compatibility
    
    This test simulates using the React client library by making similar HTTP requests
    as the actual JavaScript library would make.
    """
    
    def _authenticate(self):
        """Simulate authentication using the React client"""
        # Simulate React client authentication
        response = requests.post(
            f"{self.api_url}/auth/login",
            json={"username": self.test_username, "password": self.test_password},
            timeout=self.timeout
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, 200, "React client authentication failed")
        self.auth_token = response_data.get('token')
        self.assertIsNotNone(self.auth_token)
        
        # Headers for subsequent requests
        self.headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
    
    def _get_first_account(self):
        """Get the first account simulating React client"""
        response = requests.get(
            f"{self.api_url}/accounts",
            headers=self.headers,
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200, "Failed to get accounts")
        accounts = response.json()
        self.assertTrue(len(accounts) > 0, "No accounts found for test user")
        return accounts[0]
    
    def _get_first_card(self):
        """Get the first card simulating React client"""
        response = requests.get(
            f"{self.api_url}/cards",
            headers=self.headers,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            self.skipTest("Failed to get cards or no cards available")
            
        cards = response.json()
        if len(cards) == 0:
            self.skipTest("No cards found for test user")
        return cards[0]
    
    def test_get_account_details(self):
        """Test retrieving account details simulating React client"""
        account_id = self.test_account.get('id')
        response = requests.get(
            f"{self.api_url}/accounts/{account_id}",
            headers=self.headers,
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200, "Failed to get account details")
        account_details = response.json()
        self.assertEqual(account_details.get('id'), account_id)
        self.assertIsNotNone(account_details.get('accountNumber'))
    
    def test_get_account_balance(self):
        """Test retrieving account balance simulating React client"""
        account_id = self.test_account.get('id')
        response = requests.get(
            f"{self.api_url}/accounts/{account_id}/balance",
            headers=self.headers,
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200, "Failed to get account balance")
        balance = response.json()
        self.assertIsNotNone(balance.get('currentBalance'))
        self.assertIsNotNone(balance.get('availableBalance'))


class AngularClientTest(BaseCrossPlatformTest):
    """
    Test suite for Angular client compatibility
    
    This test simulates using the Angular client library by making similar HTTP requests
    as the actual TypeScript library would make.
    """
    
    def _authenticate(self):
        """Simulate authentication using the Angular client"""
        # Similar to React implementation, simulating Angular HTTP Client
        response = requests.post(
            f"{self.api_url}/auth/login",
            json={"username": self.test_username, "password": self.test_password},
            timeout=self.timeout
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, 200, "Angular client authentication failed")
        self.auth_token = response_data.get('token')
        self.assertIsNotNone(self.auth_token)
        
        # Headers for subsequent requests
        self.headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
    
    def _get_first_account(self):
        """Get the first account simulating Angular client"""
        response = requests.get(
            f"{self.api_url}/accounts",
            headers=self.headers,
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200, "Failed to get accounts")
        accounts = response.json()
        self.assertTrue(len(accounts) > 0, "No accounts found for test user")
        return accounts[0]
    
    def _get_first_card(self):
        """Get the first card simulating Angular client"""
        response = requests.get(
            f"{self.api_url}/cards",
            headers=self.headers,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            self.skipTest("Failed to get cards or no cards available")
            
        cards = response.json()
        if len(cards) == 0:
            self.skipTest("No cards found for test user")
        return cards[0]
    
    def test_get_account_details(self):
        """Test retrieving account details simulating Angular client"""
        account_id = self.test_account.get('id')
        response = requests.get(
            f"{self.api_url}/accounts/{account_id}",
            headers=self.headers,
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200, "Failed to get account details")
        account_details = response.json()
        self.assertEqual(account_details.get('id'), account_id)
        self.assertIsNotNone(account_details.get('accountNumber'))


class VueClientTest(BaseCrossPlatformTest):
    """
    Test suite for Vue.js client compatibility
    
    This test simulates using the Vue.js client library by making similar HTTP requests
    as the actual JavaScript library would make.
    """
    
    def _authenticate(self):
        """Simulate authentication using the Vue client"""
        # Similar to React implementation, simulating Vue Fetch API
        response = requests.post(
            f"{self.api_url}/auth/login",
            json={"username": self.test_username, "password": self.test_password},
            timeout=self.timeout
        )
        
        response_data = response.json()
        self.assertEqual(response.status_code, 200, "Vue client authentication failed")
        self.auth_token = response_data.get('token')
        self.assertIsNotNone(self.auth_token)
        
        # Headers for subsequent requests
        self.headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
    
    def _get_first_account(self):
        """Get the first account simulating Vue client"""
        response = requests.get(
            f"{self.api_url}/accounts",
            headers=self.headers,
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200, "Failed to get accounts")
        accounts = response.json()
        self.assertTrue(len(accounts) > 0, "No accounts found for test user")
        return accounts[0]
    
    def _get_first_card(self):
        """Get the first card simulating Vue client"""
        response = requests.get(
            f"{self.api_url}/cards",
            headers=self.headers,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            self.skipTest("Failed to get cards or no cards available")
            
        cards = response.json()
        if len(cards) == 0:
            self.skipTest("No cards found for test user")
        return cards[0]
    
    def test_get_account_details(self):
        """Test retrieving account details simulating Vue client"""
        account_id = self.test_account.get('id')
        response = requests.get(
            f"{self.api_url}/accounts/{account_id}",
            headers=self.headers,
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200, "Failed to get account details")
        account_details = response.json()
        self.assertEqual(account_details.get('id'), account_id)
        self.assertIsNotNone(account_details.get('accountNumber'))


def run_unittest_tests():
    """Run all cross-framework compatibility tests using unittest"""
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(DjangoClientTest))
    test_suite.addTest(unittest.makeSuite(ReactClientTest))
    test_suite.addTest(unittest.makeSuite(AngularClientTest))
    test_suite.addTest(unittest.makeSuite(VueClientTest))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(test_suite)
    
    print(f"\nDetailed results saved to: {output_file}")
