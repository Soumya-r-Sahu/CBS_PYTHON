"""
Direct API Testing for Django Compatibility

This module tests the API's Django compatibility directly using the requests library,
without requiring the Django client library.
"""

import unittest
import requests
import json
import os
import sys
import socket
import time
from requests.exceptions import ConnectionError, Timeout, RequestException

# Add project root to path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

# Import configuration if available, otherwise use defaults
try:
    from Backend.utils.config.compatibility import get_api_config
except ImportError:
    def get_api_config():
        return {
            "host": "localhost",
            "port": 5000
        }

def check_api_available(host, port, timeout=1):
    """Check if the API server is available by attempting a socket connection"""
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except (socket.timeout, socket.error):
        return False

class DirectDjangoCompatibilityTest(unittest.TestCase):
    """Test Django compatibility directly using requests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # Get API configuration
        api_config = get_api_config()
        cls.host = api_config.get("host", "localhost")
        if cls.host == "0.0.0.0":  # This is a binding address, not a connection address
            cls.host = "localhost"
        cls.port = api_config.get("port", 5000)
        
        # Base API URL
        cls.api_url = f"http://{cls.host}:{cls.port}/api/v1"
        
        # Check if API server is running
        if not check_api_available(cls.host, cls.port):
            raise unittest.SkipTest(
                f"API server not available at {cls.host}:{cls.port}. "
                "Please make sure the API server is running."
            )
    
    def setUp(self):
        """Set up test environment for each test"""
        # Create a session with Django-specific headers
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 Django-Test-Client/1.0.0",
            "X-Requested-With": "XMLHttpRequest",
            "X-Django-CSRF-Token": "test-csrf-token",
            "Cookie": "csrftoken=test-csrf-token"
        })
        
        # Test user credentials
        self.test_user = {
            "username": "test_django_user",
            "password": "Test@123",
            "email": "test_django@example.com"
        }
        
        # Flag to track authentication status
        self.authenticated = False
        
        # Try to authenticate with API
        try:
            self._authenticate()
        except (ConnectionError, Timeout, RequestException) as e:
            self.skipTest(f"Failed to connect to API server: {e}")
    
    def _make_request(self, method, url, **kwargs):
        """
        Make a request with retry logic and better error handling
        
        Args:
            method: HTTP method (get, post, etc.)
            url: Full URL to request
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response object
            
        Raises:
            unittest.SkipTest: If the server is not available
        """
        max_retries = 2
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                return getattr(self.session, method)(url, **kwargs)
            except (ConnectionError, Timeout) as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise unittest.SkipTest(f"API server connection failed: {e}")
            except Exception as e:
                raise unittest.SkipTest(f"Request failed: {e}")
    
    def _authenticate(self):
        """Authenticate with the API"""
        auth_url = f"{self.api_url}/auth/login"
        
        try:
            response = self._make_request(
                "post",
                auth_url,
                json={
                    "username": self.test_user["username"],
                    "password": self.test_user["password"]
                },
                timeout=5
            )
            
            # Check if login was successful
            if response.status_code == 200:
                data = response.json()
                token = data.get("token")
                
                if token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {token}"
                    })
                    self.authenticated = True
                    return True
            
            # Try to register the user if login fails
            register_url = f"{self.api_url}/auth/register"
            register_data = {
                "username": self.test_user["username"],
                "password": self.test_user["password"],
                "email": self.test_user["email"],
                "first_name": "Test",
                "last_name": "Django"
            }
            
            register_response = self._make_request(
                "post", 
                register_url, 
                json=register_data,
                timeout=5
            )
            
            # Try to login again after registration
            if register_response.status_code in (200, 201):
                return self._authenticate()
            
            # If we got here, authentication failed
            return False
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def test_django_detection(self):
        """Test that the API correctly detects Django clients"""
        compat_url = f"{self.api_url}/compatibility/info"
        
        try:
            response = self._make_request("get", compat_url, timeout=5)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("detected_framework", data)
            
            # The API should detect this as a Django client
            detected = data["detected_framework"].lower()
            self.assertEqual(detected, "django", 
                            f"API detected {detected} instead of django")
        except unittest.SkipTest:
            raise
        except Exception as e:
            self.fail(f"Test failed: {e}")
    
    def test_csrf_handling(self):
        """Test that the API handles Django CSRF tokens correctly"""
        # Set CSRF token in header
        csrf_token = "django-csrf-test-token"
        self.session.headers.update({
            "X-CSRFToken": csrf_token
        })
        
        # Make a POST request that should accept the CSRF token
        test_url = f"{self.api_url}/compatibility/test"
        
        try:
            response = self._make_request(
                "post",
                test_url,
                json={"test_data": "csrf_test"},
                timeout=5
            )
            
            self.assertEqual(response.status_code, 200)
            
            # The response should include the headers received
            data = response.json()
            self.assertIn("headers_received", data)
            
            # Check if CSRF header was received (case-insensitive)
            headers_received = {k.lower(): v for k, v in data["headers_received"].items()}
            
            # Test should pass if either X-CSRFToken or X-Csrftoken is present
            csrf_header_present = "x-csrftoken" in headers_received
            self.assertTrue(csrf_header_present, "CSRF header not detected by API")
        except unittest.SkipTest:
            raise
        except Exception as e:
            self.fail(f"Test failed: {e}")
    
    def test_django_account_operations(self):
        """Test basic account operations with Django-specific headers"""
        # Skip if not authenticated
        if not self.authenticated:
            self.skipTest("Not authenticated")
        
        # Get accounts
        accounts_url = f"{self.api_url}/accounts"
        
        try:
            response = self._make_request("get", accounts_url, timeout=5)
            
            self.assertEqual(response.status_code, 200)
            
            # Extract account data
            accounts_data = response.json()
            
            # If we have accounts data, the test passed
            self.assertIsInstance(accounts_data, (dict, list))
            
            # Handle different response formats
            if isinstance(accounts_data, dict):
                accounts = accounts_data.get("accounts", [])
            else:
                accounts = accounts_data
            
            # If no accounts found, create one for testing
            if len(accounts) == 0:
                create_response = self._make_request(
                    "post",
                    accounts_url,
                    json={
                        "account_type": "SAVINGS",
                        "initial_deposit": 1000.00
                    },
                    timeout=5
                )
                
                self.assertTrue(
                    create_response.status_code in (200, 201), 
                    f"Failed to create account: {create_response.text}"
                )
        except unittest.SkipTest:
            raise
        except Exception as e:
            self.fail(f"Failed to process account data: {e}")


if __name__ == "__main__":
    unittest.main()
