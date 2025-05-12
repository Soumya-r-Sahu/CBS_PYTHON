"""
Security Headers Middleware for Core Banking System

This middleware adds important security headers to HTTP responses
to protect against common web vulnerabilities.
"""

import logging
from functools import wraps
from flask import request, Flask

# Configure logger
logger = logging.getLogger(__name__)


def add_security_headers(app: Flask):
    """
    Configure Flask application to add security headers to all responses.
    
    Args:
        app (Flask): The Flask application instance
    """
    @app.after_request
    def apply_security_headers(response):
        """
        Add security headers to the HTTP response.
        
        Args:
            response: Flask response object
            
        Returns:
            Modified response with security headers
        """
        # Content Security Policy (CSP)
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'"
        )
        
        # Cross-Origin Resource Sharing (CORS) headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        # Other security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), interest-cohort=()'
        
        # Remove headers that might expose server details
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)
        
        return response
    
    logger.info("Security headers configured for all responses")
    return app


def content_security_policy(policy=None):
    """
    Decorator to add a custom Content Security Policy (CSP) header to specific routes.
    
    Args:
        policy (str): Custom CSP policy
        
    Returns:
        Decorator function
    """
    if policy is None:
        policy = "default-src 'self'"
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Add CSP header to response
            if isinstance(response, tuple):
                # Response is (response_object, status_code)
                response[0].headers['Content-Security-Policy'] = policy
            else:
                # Response is just the response object
                response.headers['Content-Security-Policy'] = policy
            
            return response
        
        return decorated_function
    
    return decorator
