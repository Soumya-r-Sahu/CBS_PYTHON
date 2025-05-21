"""
CORS Middleware Module

This module provides Cross-Origin Resource Sharing (CORS) middleware.
"""

import logging
import functools
from typing import Dict, List, Any, Optional, Callable, Set
from flask import Flask, request, Response, current_app

# Import configuration
try:
    from security.config import CORS_CONFIG
except ImportError:
    # Fallback configuration
    def get_cors_settings():
        return {
            "allowed_origins": ["http://localhost:3000"],
            "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allowed_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Length", "X-Request-Id"],
            "supports_credentials": True,
            "max_age": 600,  # Preflight cache time in seconds
        }
    
    CORS_CONFIG = get_cors_settings()

# Configure logger
logger = logging.getLogger(__name__)


class CORSMiddleware:
    """
    CORS middleware for Flask applications
    
    This middleware handles Cross-Origin Resource Sharing (CORS) headers
    to allow browsers to make cross-origin requests safely.
    """
    
    def __init__(self, app=None):
        """
        Initialize the CORS middleware
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize with Flask application
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Handle OPTIONS requests
        app.before_request(self._handle_preflight)
        
        # Add CORS headers to all responses
        app.after_request(self._add_cors_headers)
    
    def _handle_preflight(self):
        """
        Handle preflight OPTIONS requests
        
        Returns:
            Response for OPTIONS requests, None otherwise
        """
        if request.method != 'OPTIONS':
            return None
        
        # Get origin
        origin = request.headers.get('Origin')
        if not origin:
            return None
        
        # Check if origin is allowed
        allowed_origins = CORS_CONFIG["allowed_origins"]
        if not self._is_origin_allowed(origin, allowed_origins):
            logger.warning(f"CORS preflight request from disallowed origin: {origin}")
            return Response('', 204)
        
        # Create response
        response = Response('', 204)
        
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = ', '.join(CORS_CONFIG["allowed_methods"])
        
        # Add allowed headers
        response.headers['Access-Control-Allow-Headers'] = ', '.join(CORS_CONFIG["allowed_headers"])
        
        # Add exposed headers if configured
        if CORS_CONFIG.get("expose_headers"):
            response.headers['Access-Control-Expose-Headers'] = ', '.join(CORS_CONFIG["expose_headers"])
        
        # Add credentials support if configured
        if CORS_CONFIG.get("supports_credentials"):
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Add max age if configured
        if CORS_CONFIG.get("max_age"):
            response.headers['Access-Control-Max-Age'] = str(CORS_CONFIG["max_age"])
        
        return response
    
    def _add_cors_headers(self, response: Response) -> Response:
        """
        Add CORS headers to response
        
        Args:
            response: Flask response
            
        Returns:
            Response with CORS headers
        """
        # Get origin
        origin = request.headers.get('Origin')
        if not origin:
            return response
        
        # Check if origin is allowed
        allowed_origins = CORS_CONFIG["allowed_origins"]
        if not self._is_origin_allowed(origin, allowed_origins):
            return response
        
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = origin
        
        # Add credentials support if configured
        if CORS_CONFIG.get("supports_credentials"):
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Add exposed headers if configured
        if CORS_CONFIG.get("expose_headers"):
            response.headers['Access-Control-Expose-Headers'] = ', '.join(CORS_CONFIG["expose_headers"])
        
        return response
    
    def _is_origin_allowed(self, origin: str, allowed_origins: List[str]) -> bool:
        """
        Check if an origin is allowed
        
        Args:
            origin: Origin to check
            allowed_origins: List of allowed origins
            
        Returns:
            True if allowed, False otherwise
        """
        # Special case: wildcard
        if '*' in allowed_origins:
            return True
        
        # Exact match
        if origin in allowed_origins:
            return True
        
        # Domain wildcard (e.g., *.example.com)
        for allowed in allowed_origins:
            if allowed.startswith('*.'):
                domain = allowed[2:]  # Remove *. prefix
                if origin.endswith(domain) and origin.startswith('http'):
                    return True
        
        return False


def cors_protected(allowed_origins=None, allowed_methods=None, allowed_headers=None):
    """
    Decorator for adding CORS headers to specific routes
    
    Args:
        allowed_origins: List of allowed origins
        allowed_methods: List of allowed methods
        allowed_headers: List of allowed headers
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            # Execute the original function
            result = f(*args, **kwargs)
            
            # If result is a tuple (response, status_code), extract response
            if isinstance(result, tuple) and len(result) >= 1:
                response = result[0]
                status_code = result[1] if len(result) >= 2 else 200
            else:
                response = result
                status_code = 200
            
            # Get origin
            origin = request.headers.get('Origin')
            if not origin:
                return result
            
            # Check if origin is allowed
            origins_to_check = allowed_origins or CORS_CONFIG["allowed_origins"]
            middleware = CORSMiddleware()
            if not middleware._is_origin_allowed(origin, origins_to_check):
                return result
            
            # Add CORS headers
            if hasattr(response, 'headers'):
                response.headers['Access-Control-Allow-Origin'] = origin
                
                # Add credentials support if configured
                if CORS_CONFIG.get("supports_credentials"):
                    response.headers['Access-Control-Allow-Credentials'] = 'true'
                
                # Add exposed headers if configured
                if CORS_CONFIG.get("expose_headers"):
                    response.headers['Access-Control-Expose-Headers'] = ', '.join(CORS_CONFIG["expose_headers"])
            
            return result
            
        return wrapped
    
    return decorator
