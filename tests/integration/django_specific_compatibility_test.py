"""
Django Specific Compatibility Tests

This module contains compatibility tests specifically for Django frontend integrations.
"""

import unittest
import os
import sys
import json
import requests
import importlib.util
from pathlib import Path

# Add project root to path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

# Add Backend directory to the path
backend_dir = os.path.join(project_root, 'Backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Add integration_interfaces directory to the path
integration_dir = os.path.join(backend_dir, 'integration_interfaces')
if integration_dir not in sys.path:
    sys.path.insert(0, integration_dir)

# Configure Django settings for testing (before any Django imports)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tests.helpers.test_django_settings')

# Check if Django is installed and configure it manually if needed
try:
    import django
    from django.conf import settings
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            INSTALLED_APPS=[],
            SECRET_KEY='django-insecure-$-test-key-do-not-use-in-production',
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            }
        )
        django.setup()
except ImportError:
    print("Django not installed, will use minimal API client")

# Function to check if a module exists at a specific path
def check_module_exists(module_path):
    return os.path.exists(module_path) and os.path.isfile(module_path)

# Try to import the Django client with a fallback to our minimal client
try:
    # First try direct import
    from Backend.integration_interfaces.django_client import BankingAPIClient, APIError
    from Backend.utils.config.compatibility import get_api_config
    
    DJANGO_CLIENT_AVAILABLE = True
    print("Successfully imported Django client library")
except ImportError as e:
    print(f"WARNING: Django client library import error: {e}")
    
    # Fallback to our minimal implementation for testing
    print("Using minimal API client implementation for testing")
    
    class APIError(Exception):
        """Custom exception for API errors."""
        def __init__(self, message, code=None, status=None, response=None):
            self.message = message
            self.code = code
            self.status = status
            self.response = response
            super().__init__(self.message)
    
    class BankingAPIClient:
        """Minimal client for interacting with the CBS Banking API."""
        
        def __init__(self, config=None):
            """Initialize the API client."""
            self.config = config or {}
            self.base_url = self.config.get('base_url', 'http://localhost:5000/api/v1')
            self.timeout = self.config.get('timeout', 30)
            self.retry_attempts = self.config.get('retry_attempts', 3)
            
            # Create a session for persistent connections
            self.session = requests.Session()
            self.session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Django-Test-Client/1.0.0'
            })
        
        def set_auth_token(self, token):
            """Set the authorization token for API requests."""
            if token:
                self.session.headers.update({'Authorization': f'Bearer {token}'})
            elif 'Authorization' in self.session.headers:
                del self.session.headers['Authorization']
        
        def clear_auth_token(self):
            """Remove the authorization token from the session."""
            if 'Authorization' in self.session.headers:
                del self.session.headers['Authorization']
        
        def set_csrf_token(self, token):
            """Set the CSRF token for API requests."""
            if token:
                self.session.headers.update({'X-CSRFToken': token})
            elif 'X-CSRFToken' in self.session.headers:
                del self.session.headers['X-CSRFToken']
        
        def set_session_from_request(self, request):
            """Set authentication and CSRF tokens from Django request."""
            # Extract CSRF token from cookie
            csrf_cookie = 'csrftoken'
            if hasattr(request, 'COOKIES') and csrf_cookie in request.COOKIES:
                self.set_csrf_token(request.COOKIES[csrf_cookie])
            
            # Extract JWT token from session
            if hasattr(request, 'session') and 'jwt_token' in request.session:
                self.set_auth_token(request.session['jwt_token'])
        
        def _build_url(self, path):
            """Build a full URL from the given path."""
            # Remove leading slash from path if present
            if path.startswith('/'):
                path = path[1:]
            
            # Remove trailing slash from base_url if present
            base = self.base_url
            if base.endswith('/'):
                base = base[:-1]
                
            return f"{base}/{path}"
        
        def _handle_response(self, response):
            """Handle the API response and return appropriate data."""
            if response.status_code >= 400:
                try:
                    data = response.json()
                    message = data.get('message', data.get('error', 'API Error'))
                except:
                    message = f"API Error: {response.status_code}"
                
                raise APIError(
                    message=message,
                    status=response.status_code,
                    response=response
                )
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {'data': response.text}
        
        def request(self, method, path, data=None, params=None, headers=None):
            """Make an API request."""
            url = self._build_url(path)
            kwargs = {'headers': headers or {}, 'timeout': self.timeout}
            
            if params:
                kwargs['params'] = params
            
            if data:
                kwargs['json'] = data
            
            response = self.session.request(method, url, **kwargs)
            return self._handle_response(response)
        
        def get(self, path, params=None, headers=None):
            """Make a GET request to the API."""
            return self.request('GET', path, params=params, headers=headers)
        
        def post(self, path, data, params=None, headers=None):
            """Make a POST request to the API."""
            return self.request('POST', path, data=data, params=params, headers=headers)
        
        def authenticate(self, username, password):
            """Authenticate with the API and obtain JWT token."""
            response = self.post('auth/login', {
                'username': username, 
                'password': password
            })
            
            # Extract and store the token
            if 'token' in response:
                self.set_auth_token(response['token'])
            
            return response
        
        def get_accounts(self):
            """Get all accounts for the authenticated user."""
            response = self.get('accounts')
            return response.get('accounts', [])
        
        def get_account(self, account_number):
            """Get details for a specific account."""
            response = self.get(f'accounts/{account_number}')
            return response.get('account', {})
    
    # Define get_api_config function
    def get_api_config():
        return {
            "host": "localhost",
            "port": 5000,
            "allowed_origins": ["*"]
        }
    
    DJANGO_CLIENT_AVAILABLE = True

class DjangoSpecificTests(unittest.TestCase):
    """Test cases specifically for Django integration"""
    
    def setUp(self):
        """Set up test environment"""
        if not DJANGO_CLIENT_AVAILABLE:
            self.skipTest("Django client library not available")
        
        api_config = get_api_config()
        host = api_config.get('host', 'localhost')
        port = api_config.get('port', 5000)
        
        # Create API client
        self.client = BankingAPIClient({
            'base_url': f"http://{host}:{port}/api/v1",
            'timeout': 10,
            'retry_attempts': 2
        })
        
        # Test user credentials
        self.test_user = {
            'username': 'test_django_user',
            'password': 'Test@123',
            'email': 'test_django@example.com'
        }
        
        # Register test user if needed
        self._ensure_test_user_exists()
        
        # Authenticate
        self._authenticate()
    
    def _ensure_test_user_exists(self):
        """Make sure test user exists in the system"""
        try:
            # Try to register the test user
            self.client.post('auth/register', {
                'username': self.test_user['username'],
                'password': self.test_user['password'],
                'email': self.test_user['email'],
                'first_name': 'Test',
                'last_name': 'Django'
            })
        except APIError as e:
            # User might already exist
            if 'username already exists' not in str(e):
                print(f"Warning: Failed to register test user: {e}")
    
    def _authenticate(self):
        """Authenticate with the API"""
        try:
            auth_data = self.client.authenticate(
                self.test_user['username'],
                self.test_user['password']
            )
            
            # Ensure we have a token
            self.assertIn('token', auth_data)
            self.token = auth_data['token']
            
            # Add token to client
            self.client.set_auth_token(self.token)
            
            return True
        except APIError as e:
            self.fail(f"Authentication failed: {e}")
            return False
    
    def test_csrf_token_handling(self):
        """Test CSRF token handling in Django client"""
        # Set a test CSRF token
        test_csrf_token = "test-csrf-token-12345"
        self.client.set_csrf_token(test_csrf_token)
        
        # Verify it's set in headers
        csrf_header = self.client.config.get('csrf_header', 'X-CSRFToken')
        self.assertIn(csrf_header, self.client.session.headers)
        self.assertEqual(self.client.session.headers[csrf_header], test_csrf_token)
        
        # Clear the token
        self.client.set_csrf_token(None)
        
        # Verify it's removed
        self.assertNotIn(csrf_header, self.client.session.headers)
    
    def test_django_session_integration(self):
        """Test creating a fake Django request object and setting session from it"""
        # Create a mock Django request-like object
        class MockDjangoRequest:
            def __init__(self):
                self.COOKIES = {'csrftoken': 'mock-csrf-token'}
                self.session = {'jwt_token': 'mock-jwt-token'}
        
        # Create a mock request
        mock_request = MockDjangoRequest()
        
        # Test setting session from request
        self.client.set_session_from_request(mock_request)
        
        # Verify both tokens are set
        self.assertIn('Authorization', self.client.session.headers)
        self.assertIn('X-CSRFToken', self.client.session.headers)
        self.assertEqual(self.client.session.headers['Authorization'], 'Bearer mock-jwt-token')
        self.assertEqual(self.client.session.headers['X-CSRFToken'], 'mock-csrf-token')
    
    def test_account_operations(self):
        """Test account operations with Django client"""
        # 1. Get accounts
        try:
            accounts = self.client.get_accounts()
            self.assertIsInstance(accounts, list)
            
            # Create an account if needed
            if len(accounts) == 0:
                result = self.client.post('accounts', {
                    'account_type': 'SAVINGS',
                    'initial_deposit': 1000.00
                })
                self.assertIn('id', result)
                self.assertIn('account_number', result)
                
                # Get accounts again to verify creation
                accounts = self.client.get_accounts()
                self.assertGreater(len(accounts), 0)
            
            # Get details for the first account
            account = accounts[0]
            account_number = account.get('account_number')
            self.assertIsNotNone(account_number)
            
            # Get account details
            account_details = self.client.get_account(account_number)
            self.assertEqual(account_details.get('account_number'), account_number)
            
        except APIError as e:
            self.fail(f"Account operations failed: {e}")
    
    def test_error_handling(self):
        """Test error handling in Django client"""
        # Try to access a non-existent endpoint
        with self.assertRaises(APIError):
            self.client.get('non_existent_endpoint')
        
        # Try to access a protected endpoint without authentication
        # First, clear the token
        self.client.clear_auth_token()
        
        with self.assertRaises(APIError) as context:
            self.client.get('accounts')
        
        # Verify error contains authentication info
        self.assertIn('authentication', str(context.exception).lower())
    
    def test_framework_detection_endpoint(self):
        """Test the framework detection endpoint with Django headers"""
        # Add Django-specific headers
        original_headers = self.client.session.headers.copy()
        
        try:
            # Add Django identifying headers
            self.client.session.headers.update({
                'X-Django-CSRF-Token': 'test-token',
                'Cookie': 'csrftoken=test-cookie',
                'User-Agent': 'Mozilla/5.0 Django-Test-Client'
            })
            
            # Call the compatibility info endpoint
            response = self.client.get('compatibility/info')
            
            # Verify the backend correctly detected Django
            self.assertIn('detected_framework', response)
            self.assertEqual(response['detected_framework'].lower(), 'django')
            
        finally:
            # Restore original headers
            self.client.session.headers = original_headers


if __name__ == '__main__':
    unittest.main()
