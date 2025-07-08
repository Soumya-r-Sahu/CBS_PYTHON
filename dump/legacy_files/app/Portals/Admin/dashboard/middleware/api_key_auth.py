"""
API Key Authentication Middleware

This module provides middleware for API key authentication in the Admin module.
"""
import os
import logging
from typing import Dict, List, Any, Optional, Callable
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)

class APIKeyAuthentication:
    """Middleware for API key authentication."""
    
    def __init__(self, get_response: Callable):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response
        
        # Load API keys from environment or settings
        self.api_keys = getattr(settings, 'MODULE_API_KEYS', {})
        
        # Load from environment variables (CBS_API_KEY_<MODULE_ID>)
        for key, value in os.environ.items():
            if key.startswith('CBS_API_KEY_'):
                module_id = key[len('CBS_API_KEY_'):].lower()
                self.api_keys[module_id] = value
        
        # Set a master key for internal services
        self.master_key = os.environ.get('CBS_ADMIN_MASTER_KEY', getattr(settings, 'ADMIN_MASTER_KEY', None))
        
        if not self.master_key:
            logger.warning("No master API key configured. Some internal services may not work.")
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process the request.
        
        Args:
            request: The HTTP request
            
        Returns:
            The HTTP response
        """
        # Skip authentication for non-API paths
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key')
        module_id = request.headers.get('X-Module-ID')
        
        # If no API key provided, deny access
        if not api_key:
            return JsonResponse({
                'status': 'error',
                'message': 'API key required'
            }, status=401)
        
        # Check if it's the master key
        if self.master_key and api_key == self.master_key:
            # Master key has access to everything
            request.is_admin_service = True
            return self.get_response(request)
        
        # Check module-specific API key
        if module_id and module_id in self.api_keys:
            if api_key == self.api_keys[module_id]:
                # Valid module API key
                request.module_id = module_id
                return self.get_response(request)
        
        # API key is invalid
        logger.warning(f"Invalid API key used for module: {module_id}")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid API key'
        }, status=401)


def get_api_key_for_module(module_id: str) -> Optional[str]:
    """
    Get the API key for a specific module.
    
    Args:
        module_id: ID of the module
        
    Returns:
        The API key if found, None otherwise
    """
    # Check environment variables
    env_key = f"CBS_API_KEY_{module_id.upper()}"
    if env_key in os.environ:
        return os.environ[env_key]
    
    # Check settings
    from django.conf import settings
    api_keys = getattr(settings, 'MODULE_API_KEYS', {})
    return api_keys.get(module_id)


def validate_api_key(api_key: str, module_id: str = None) -> bool:
    """
    Validate an API key.
    
    Args:
        api_key: The API key to validate
        module_id: Optional module ID to validate against
        
    Returns:
        True if valid, False otherwise
    """
    # Check if it's the master key
    master_key = os.environ.get('CBS_ADMIN_MASTER_KEY')
    if master_key and api_key == master_key:
        return True
    
    # If module_id provided, check module-specific key
    if module_id:
        module_key = get_api_key_for_module(module_id)
        if module_key and api_key == module_key:
            return True
    
    # Check against all module keys
    from django.conf import settings
    api_keys = getattr(settings, 'MODULE_API_KEYS', {})
    return api_key in api_keys.values()
