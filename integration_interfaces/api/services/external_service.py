"""
External Service Client for Core Banking System

This module provides a client for communicating with external banking services.
It implements environment-specific timeout handling and connection settings.
"""
import os
import sys
import logging
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Union
from requests.exceptions import RequestException, Timeout, ConnectionError

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

# Import environment functions with fallback
try:
    from utils.config.environment import (
        get_environment_name, is_production, is_development, is_test,
        is_debug_enabled, env_aware
    )
except ImportError:
    try:
        from app.config.environment import (
            get_environment_name, is_production, is_development, is_test,
            is_debug_enabled, env_aware
        )
    except ImportError:
        # Minimal fallback implementation
        def get_environment_name(): return os.environ.get("CBS_ENVIRONMENT", "development")
        def is_production(): return get_environment_name() == "production"
        def is_development(): return get_environment_name() == "development" 
        def is_test(): return get_environment_name() == "test"
        def is_debug_enabled(): return os.environ.get("DEBUG", "0").lower() in ("1", "true", "yes")
        def env_aware(func): return func
except ImportError:
    # Fallback environment detection
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    def is_production(): return env_str == "production"
    def is_development(): return env_str == "development"
    def is_test(): return env_str == "test"
    def get_environment_name(): return env_str.capitalize()
    def is_debug_enabled(): return os.environ.get("CBS_DEBUG", "false").lower() == "true"
    def env_aware(development=None, test=None, production=None):
        if is_production():
            return production
        elif is_test(): 
            return test
        else:
            return development

# Try to import config
try:
    from config import API_CONFIG
except ImportError:
    # Default configuration if config module is not available
    API_CONFIG = {
        "external_services": {
            "base_url": os.environ.get("CBS_EXTERNAL_API_URL", "https://api.banking.example.com"),
            "api_key": os.environ.get("CBS_EXTERNAL_API_KEY", ""),
            "api_secret": os.environ.get("CBS_EXTERNAL_API_SECRET", ""),
        }
    }

# Configure logger
logger = logging.getLogger(__name__)

class ExternalServiceClient:
    """
    Client for interacting with external banking services.
    Provides environment-specific timeout handling and retry mechanisms.
    """
    
    def __init__(self, service_name: str = "default"):
        """
        Initialize the external service client with proper environment configuration
        
        Args:
            service_name: Name of the specific external service to connect to
        """
        # Load service configuration
        self.service_name = service_name
        self.base_config = API_CONFIG.get("external_services", {})
        self.service_config = self.base_config.get(service_name, {})
        
        # Set base URL with environment-specific domain if available
        if is_production():
            self.base_url = self.service_config.get("production_url", self.base_config.get("base_url", ""))
        else:
            # Use sandbox in non-production environments
            self.base_url = self.service_config.get("sandbox_url", self.base_config.get("sandbox_url", self.base_config.get("base_url", "")))
        
        # Authentication details
        self.api_key = self.service_config.get("api_key", self.base_config.get("api_key", ""))
        self.api_secret = self.service_config.get("api_secret", self.base_config.get("api_secret", ""))
        
        # Configure environment-specific timeouts
        # Each environment gets appropriate timeout values:
        # - Production: Shorter timeouts for better user experience but not too short
        # - Test: Medium timeouts to catch slow responses
        # - Development: Longer timeouts for debugging
        self._configure_timeouts()
        
        # Configure environment-specific retry settings
        self._configure_retries()
        
        # Set up session
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key,
            "User-Agent": f"CBS-Banking/{get_environment_name()}"
        })
        
        logger.info(f"Initialized ExternalServiceClient for {service_name} in {get_environment_name()} environment")
        
    def _configure_timeouts(self):
        """Configure environment-specific timeout settings"""
        # Get timeout values from configuration or environment variables
        # If not explicitly defined, use environment-specific defaults
        
        # Connection timeout: Time to establish connection
        self.connect_timeout = env_aware(
            development=int(os.environ.get("CBS_API_CONNECT_TIMEOUT", self.service_config.get("connect_timeout", 10))),
            test=int(os.environ.get("CBS_API_CONNECT_TIMEOUT", self.service_config.get("connect_timeout", 5))),
            production=int(os.environ.get("CBS_API_CONNECT_TIMEOUT", self.service_config.get("connect_timeout", 3)))
        )
        
        # Read timeout: Time to receive response
        self.read_timeout = env_aware(
            development=int(os.environ.get("CBS_API_READ_TIMEOUT", self.service_config.get("read_timeout", 60))),
            test=int(os.environ.get("CBS_API_READ_TIMEOUT", self.service_config.get("read_timeout", 30))),
            production=int(os.environ.get("CBS_API_READ_TIMEOUT", self.service_config.get("read_timeout", 20)))
        )
        
        # Total timeout: Overall request timeout (connection + read)
        self.total_timeout = env_aware(
            development=int(os.environ.get("CBS_API_TOTAL_TIMEOUT", self.service_config.get("total_timeout", 120))),
            test=int(os.environ.get("CBS_API_TOTAL_TIMEOUT", self.service_config.get("total_timeout", 60))),
            production=int(os.environ.get("CBS_API_TOTAL_TIMEOUT", self.service_config.get("total_timeout", 30)))
        )
    
    def _configure_retries(self):
        """Configure environment-specific retry settings"""
        # Number of retry attempts on failure
        self.max_retries = env_aware(
            development=int(os.environ.get("CBS_API_MAX_RETRIES", self.service_config.get("max_retries", 3))),
            test=int(os.environ.get("CBS_API_MAX_RETRIES", self.service_config.get("max_retries", 2))),
            production=int(os.environ.get("CBS_API_MAX_RETRIES", self.service_config.get("max_retries", 2)))
        )
        
        # Initial delay before first retry (seconds)
        self.retry_delay = env_aware(
            development=float(os.environ.get("CBS_API_RETRY_DELAY", self.service_config.get("retry_delay", 1.0))),
            test=float(os.environ.get("CBS_API_RETRY_DELAY", self.service_config.get("retry_delay", 0.5))),
            production=float(os.environ.get("CBS_API_RETRY_DELAY", self.service_config.get("retry_delay", 0.2)))
        )
        
        # Retry backoff factor
        self.retry_backoff = env_aware(
            development=float(os.environ.get("CBS_API_RETRY_BACKOFF", self.service_config.get("retry_backoff", 2.0))),
            test=float(os.environ.get("CBS_API_RETRY_BACKOFF", self.service_config.get("retry_backoff", 1.5))),
            production=float(os.environ.get("CBS_API_RETRY_BACKOFF", self.service_config.get("retry_backoff", 1.5)))
        )
    
    def request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, 
                headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None,
                timeout: Optional[Union[float, tuple]] = None) -> Dict[str, Any]:
        """
        Make a request to the external API with proper timeout and retry handling
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request payload
            headers: Additional headers
            params: URL parameters
            timeout: Custom timeout (overrides defaults)
            
        Returns:
            API response data
            
        Raises:
            RequestException: If request fails after all retries
        """
        # If custom timeout not provided, use environment-specific configured values
        if timeout is None:
            timeout = (self.connect_timeout, self.read_timeout)
            
        # Build full URL
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Prepare request headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
            
        # Add environment marker to non-production requests
        if not is_production():
            env_name = "TEST" if is_test() else "DEV"
            request_headers["X-Environment"] = env_name
            
        # Initialize retry counter
        retries = 0
        delay = self.retry_delay
        
        while True:
            try:
                # Make the request with environment-specific timeout
                start_time = time.time()
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=request_headers,
                    params=params,
                    timeout=timeout
                )
                
                # Log request duration in debug mode
                if is_debug_enabled():
                    duration = time.time() - start_time
                    logger.debug(f"Request to {url} completed in {duration:.2f}s")
                
                # Raise for HTTP errors
                response.raise_for_status()
                
                # Return the response data
                return response.json()
                
            except (Timeout, ConnectionError) as e:
                # Handle timeout and connection errors with retry logic
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"Failed to connect to {url} after {retries} attempts: {str(e)}")
                    raise
                
                # Log retry attempt
                logger.warning(f"Request to {url} failed (attempt {retries}/{self.max_retries}): {str(e)}")
                logger.info(f"Retrying in {delay:.1f} seconds...")
                
                # Wait before retrying
                time.sleep(delay)
                
                # Increase delay for next retry using backoff factor
                delay *= self.retry_backoff
                
            except RequestException as e:
                # For other request exceptions (HTTP errors, etc.)
                logger.error(f"Request to {url} failed: {str(e)}")
                
                # Only retry on certain HTTP status codes 
                status_code = getattr(e.response, 'status_code', None)
                if status_code and status_code >= 500:  # Server errors might be transient
                    retries += 1
                    if retries <= self.max_retries:
                        logger.info(f"Retrying request due to server error (attempt {retries}/{self.max_retries})")
                        time.sleep(delay)
                        delay *= self.retry_backoff
                        continue
                
                # Otherwise, don't retry
                raise
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make a GET request to the external API"""
        return self.request("GET", endpoint, params=params, headers=headers)
    
    def post(self, endpoint: str, data: Dict[str, Any],
             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make a POST request to the external API"""
        return self.request("POST", endpoint, data=data, headers=headers)
    
    def put(self, endpoint: str, data: Dict[str, Any],
            headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make a PUT request to the external API"""
        return self.request("PUT", endpoint, data=data, headers=headers)
    
    def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make a DELETE request to the external API"""
        return self.request("DELETE", endpoint, headers=headers)


# Example usage
if __name__ == "__main__":
    # Simple demonstration
    client = ExternalServiceClient("payment_gateway")
    try:
        response = client.get("api/status")
        print(f"Service status: {response}")
    except Exception as e:
        print(f"Error checking service status: {str(e)}")
