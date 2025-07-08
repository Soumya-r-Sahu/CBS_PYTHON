"""
Django API Client for CBS Banking System

A client utility that Django applications can use to interact with
the Core Banking System API seamlessly.

Usage:
    from django_api_client import BankingAPIClient
    
    # Create client instance
    api_client = BankingAPIClient()
    
    # Make API calls
    accounts = api_client.get_accounts()
    
    # Call specific endpoints
    transaction = api_client.post('/transactions/transfer', {
        'from_account': '1234567890',
        'to_account': '0987654321',
        'amount': 100.00,
        'currency': 'USD',
        'description': 'Rent payment'
    })
"""

import json
import logging
import os
import requests
from typing import Any, Dict, List, Optional, Union
from requests.exceptions import RequestException, Timeout, ConnectionError

# Import Django utilities if available
try:
    from django.conf import settings
    from django.contrib.auth.models import User
    from django.http import HttpRequest
    from django.utils.translation import gettext_lazy as _
    HAS_DJANGO = True
except ImportError:
    HAS_DJANGO = False

# Try to import CBS configuration
try:
    from utils.config.compatibility import get_api_client_config
except ImportError:
    # Fallback configuration
    def get_api_client_config(framework="django"):
        return {
            "base_url": os.environ.get("CBS_API_BASE_URL", "http://localhost:5000/api/v1"),
            "timeout": 30,
            "retry_attempts": 3,
            "csrf_header": "X-CSRFToken",
            "csrf_cookie_name": "csrftoken"
        }

# Configure logger
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message, code=None, status=None, response=None):
        self.message = message
        self.code = code
        self.status = status
        self.response = response
        super().__init__(self.message)

class BankingAPIClient:
    """Client for interacting with the Core Banking System API"""
    
    def __init__(self, config=None):
        """
        Initialize the API client
        
        Args:
            config: Optional configuration dictionary to override defaults
        """
        # Load configuration
        self.config = get_api_client_config("django")
        
        # Update with provided config if any
        if config:
            self.config.update(config)
        
        # Extract commonly used config values
        self.base_url = self.config["base_url"]
        self.timeout = self.config.get("timeout", 30)
        self.retry_attempts = self.config.get("retry_attempts", 3)
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CBS-Python/Django-Client"
        })
    
    def set_auth_token(self, token):
        """
        Set the authorization token for API requests
        
        Args:
            token: JWT token string
        """
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        elif "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
    
    def clear_auth_token(self):
        """Remove the authorization token from the session"""
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
    
    def set_csrf_token(self, token):
        """
        Set the CSRF token for API requests
        
        Args:
            token: CSRF token string
        """
        csrf_header = self.config.get("csrf_header", "X-CSRFToken")
        if token:
            self.session.headers.update({csrf_header: token})
        elif csrf_header in self.session.headers:
            del self.session.headers[csrf_header]
    
    def set_session_from_request(self, request):
        """
        Set authentication and CSRF tokens from Django request
        
        Args:
            request: Django HttpRequest object
        """
        if not HAS_DJANGO:
            logger.warning("Django is not available, cannot set session from request")
            return
            
        # Extract CSRF token from cookie
        csrf_cookie = self.config.get("csrf_cookie_name", "csrftoken")
        if csrf_cookie in request.COOKIES:
            self.set_csrf_token(request.COOKIES[csrf_cookie])
        
        # Extract JWT from session if available
        if hasattr(request, "session") and "jwt_token" in request.session:
            self.set_auth_token(request.session["jwt_token"])
    
    def _build_url(self, path):
        """
        Build full URL from path
        
        Args:
            path: API endpoint path
            
        Returns:
            Full URL string
        """
        # Handle paths with or without leading slash
        if path.startswith("/"):
            path = path[1:]
        
        return f"{self.base_url}/{path}"
    
    def _handle_response(self, response):
        """
        Handle API response and extract data
        
        Args:
            response: Requests response object
            
        Returns:
            Python object from JSON response
            
        Raises:
            APIError: If the API returns an error response
        """
        try:
            data = response.json()
        except ValueError:
            # Response is not JSON
            if not response.ok:
                raise APIError(
                    f"API returned non-JSON response with status {response.status_code}",
                    status=response.status_code,
                    response=response
                )
            return response.text
        
        # Check for API errors in response
        if not response.ok or (isinstance(data, dict) and data.get("status") == "error"):
            error_message = data.get("message", "Unknown API error")
            error_code = data.get("code")
            raise APIError(
                error_message,
                code=error_code,
                status=response.status_code,
                response=response
            )
        
        return data
    
    def request(self, method, path, data=None, params=None, headers=None, retry=True):
        """
        Make an API request
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API endpoint path
            data: Request body data (will be converted to JSON)
            params: URL query parameters
            headers: Additional request headers
            retry: Whether to retry on failure
            
        Returns:
            Python object from JSON response
            
        Raises:
            APIError: If the API returns an error response
        """
        url = self._build_url(path)
        request_headers = {}
        
        # Add custom headers if provided
        if headers:
            request_headers.update(headers)
        
        # Prepare request kwargs
        kwargs = {
            "headers": request_headers,
            "timeout": self.timeout
        }
        
        # Add params and data if provided
        if params:
            kwargs["params"] = params
        
        if data:
            kwargs["json"] = data
        
        # Make the request with retries
        attempts = 0
        max_attempts = self.retry_attempts if retry else 1
        
        while attempts < max_attempts:
            attempts += 1
            
            try:
                response = self.session.request(method, url, **kwargs)
                return self._handle_response(response)
            except (Timeout, ConnectionError) as e:
                # Network error
                if attempts < max_attempts:
                    logger.warning(f"API request failed ({e.__class__.__name__}), retrying {attempts}/{max_attempts}")
                    continue
                raise APIError(f"API request failed after {max_attempts} attempts: {str(e)}")
            except RequestException as e:
                # Other request exception
                raise APIError(f"API request error: {str(e)}")
    
    # Convenience methods for common HTTP methods
    def get(self, path, params=None, headers=None):
        """
        Make a GET request to the API
        
        Args:
            path: API endpoint path
            params: URL query parameters
            headers: Additional request headers
            
        Returns:
            Python object from JSON response
        """
        return self.request("GET", path, params=params, headers=headers)
    
    def post(self, path, data, params=None, headers=None):
        """
        Make a POST request to the API
        
        Args:
            path: API endpoint path
            data: Request body data
            params: URL query parameters
            headers: Additional request headers
            
        Returns:
            Python object from JSON response
        """
        return self.request("POST", path, data=data, params=params, headers=headers)
    
    def put(self, path, data, params=None, headers=None):
        """
        Make a PUT request to the API
        
        Args:
            path: API endpoint path
            data: Request body data
            params: URL query parameters
            headers: Additional request headers
            
        Returns:
            Python object from JSON response
        """
        return self.request("PUT", path, data=data, params=params, headers=headers)
    
    def patch(self, path, data, params=None, headers=None):
        """
        Make a PATCH request to the API
        
        Args:
            path: API endpoint path
            data: Request body data
            params: URL query parameters
            headers: Additional request headers
            
        Returns:
            Python object from JSON response
        """
        return self.request("PATCH", path, data=data, params=params, headers=headers)
    
    def delete(self, path, params=None, headers=None):
        """
        Make a DELETE request to the API
        
        Args:
            path: API endpoint path
            params: URL query parameters
            headers: Additional request headers
            
        Returns:
            Python object from JSON response
        """
        return self.request("DELETE", path, params=params, headers=headers)
    
    # Banking-specific API methods
    def get_accounts(self):
        """
        Get all user accounts
        
        Returns:
            List of account objects
        """
        response = self.get("accounts")
        return response.get("data", {}).get("accounts", [])
    
    def get_account_details(self, account_number):
        """
        Get details for a specific account
        
        Args:
            account_number: Account number
            
        Returns:
            Account details
        """
        response = self.get(f"accounts/{account_number}")
        return response.get("data", {}).get("account", {})
    
    def get_transactions(self, account_number, **params):
        """
        Get transactions for an account
        
        Args:
            account_number: Account number
            **params: Filter parameters (date_from, date_to, limit, etc.)
            
        Returns:
            List of transactions
        """
        response = self.get(f"accounts/{account_number}/transactions", params=params)
        return response.get("data", {}).get("transactions", [])
    
    def transfer_money(self, from_account, to_account, amount, currency="USD", description=None):
        """
        Transfer money between accounts
        
        Args:
            from_account: Source account number
            to_account: Destination account number
            amount: Amount to transfer
            currency: Currency code (default: USD)
            description: Transaction description
            
        Returns:
            Transaction details
        """
        data = {
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "currency": currency
        }
        
        if description:
            data["description"] = description
        
        response = self.post("transactions/transfer", data)
        return response.get("data", {}).get("transaction", {})
    
    def authenticate(self, username, password, device_id=None):
        """
        Authenticate with the API and obtain JWT token
        
        Args:
            username: User's username or customer ID
            password: User's password
            device_id: Optional device identifier
            
        Returns:
            Authentication response with token
            
        Raises:
            APIError: If authentication fails
        """
        data = {
            "username": username,
            "password": password
        }
        
        if device_id:
            data["device_id"] = device_id
        
        response = self.post("auth/login", data)
        
        # Extract and store the token
        if "data" in response and "token" in response["data"]:
            self.set_auth_token(response["data"]["token"])
        
        return response["data"]
    
    def logout(self):
        """
        Log out and invalidate the current token
        
        Returns:
            Logout response
        """
        try:
            response = self.post("auth/logout", {})
            self.clear_auth_token()
            return response
        except Exception as e:
            # Always clear token even if logout fails
            self.clear_auth_token()
            raise e
