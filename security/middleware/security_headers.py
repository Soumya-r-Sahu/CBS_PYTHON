"""
Security Headers Middleware Module

This module provides middleware to add security headers to HTTP responses.
"""

import logging
from typing import Dict, Any, Optional
from flask import Flask, Response

# Configure logger
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Security headers middleware for Flask applications
    
    This middleware adds security-related HTTP headers to all responses to
    protect against common web vulnerabilities.
    """
    
    def __init__(self, app=None):
        """
        Initialize the security headers middleware
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Default security headers
        self.headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; object-src 'none'",
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize with Flask application
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Register after request handler
        app.after_request(self._process_response)
    
    def _process_response(self, response: Response) -> Response:
        """
        Add security headers to response
        
        Args:
            response: Flask response
            
        Returns:
            Response with security headers
        """
        # Add security headers
        for header, value in self.headers.items():
            response.headers[header] = value
        
        return response
    
    def update_headers(self, headers: Dict[str, str]):
        """
        Update the security headers configuration
        
        Args:
            headers: Dictionary of headers to update
        """
        self.headers.update(headers)
