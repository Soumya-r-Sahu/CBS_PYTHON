"""
Authentication Middleware Module

This module provides authentication middleware for web applications.
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from flask import Flask, request, g

# Import authentication functions
from security.common.auth import authenticate_user

# Configure logger
logger = logging.getLogger(__name__)


class AuthMiddleware:
    """
    Authentication middleware for Flask applications
    
    This middleware handles user authentication for web requests
    by validating JWT tokens in the Authorization header.
    """
    
    def __init__(self, app=None):
        """
        Initialize the authentication middleware
        
        Args:
            app: Flask application instance
        """
        self.app = app
        self.exempt_paths = []
        self.exempt_methods = ['OPTIONS']
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize with Flask application
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Register before request handler
        app.before_request(self._process_request)
    
    def exempt(self, path: str, methods: Optional[List[str]] = None):
        """
        Exempt a path from authentication
        
        Args:
            path: URL path to exempt
            methods: HTTP methods to exempt (None for all methods)
        """
        self.exempt_paths.append((path, methods))
    
    def _process_request(self):
        """
        Process the request for authentication
        
        Returns:
            Response or None (to continue processing)
        """
        # Skip for exempt paths
        for path, methods in self.exempt_paths:
            if request.path.startswith(path):
                if methods is None or request.method in methods:
                    return None
        
        # Skip for exempt methods
        if request.method in self.exempt_methods:
            return None
        
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return {'message': 'Authentication required'}, 401
        
        try:
            # Extract token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return {'message': 'Invalid authentication format'}, 401
            
            token = parts[1]
            
            # Validate token
            user = authenticate_user(token)
            if not user:
                return {'message': 'Invalid or expired token'}, 401
            
            # Store user in flask g
            g.user = user
            
            # Continue with request
            return None
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {'message': 'Authentication error'}, 401
