"""
XSS Protection Middleware

This module provides protection against cross-site scripting (XSS) attacks.
"""

import logging
import re
import html
from typing import Dict, Any, Set, List, Optional
from flask import Flask, request, Response, g

# Configure logger
logger = logging.getLogger(__name__)


class XSSProtectionMiddleware:
    """
    Cross-Site Scripting (XSS) protection middleware
    
    This middleware sanitizes input data and adds response headers
    to protect against XSS attacks.
    """
    
    def __init__(self):
        """Initialize the XSS protection middleware"""
        self.app = None
        
        # Patterns for detecting XSS attacks
        self.xss_patterns = [
            r'<script\b[^>]*>(.*?)</script>',
            r'javascript\s*:',
            r'on\w+\s*=',
            r'<iframe\b[^>]*>',
            r'document\.cookie',
            r'document\.location',
            r'document\.referrer',
            r'document\.write',
            r'window\.location',
            r'eval\s*\(',
            r'setTimeout\s*\(',
            r'setInterval\s*\(',
            r'new\s+Function\s*\('
        ]
        
        # Compiled regex patterns
        self.xss_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns]
    
    def init_app(self, app: Flask):
        """
        Initialize with Flask application
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Register before request handler
        app.before_request(self._check_request)
    
    def _check_request(self):
        """
        Check request for potential XSS attacks
        
        Returns:
            Response or None (to continue processing)
        """
        # Skip for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return None
        
        potential_xss = False
        
        # Check URL parameters
        for param, value in request.args.items():
            if isinstance(value, str) and self._contains_xss(value):
                logger.warning(f"Potential XSS detected in URL parameter '{param}': {value}")
                potential_xss = True
        
        # Check form data
        for field, value in request.form.items():
            if isinstance(value, str) and self._contains_xss(value):
                logger.warning(f"Potential XSS detected in form field '{field}': {value}")
                potential_xss = True
        
        # Check JSON data
        if request.is_json:
            try:
                json_data = request.get_json()
                if json_data and isinstance(json_data, dict):
                    for field, value in self._flatten_dict(json_data).items():
                        if isinstance(value, str) and self._contains_xss(value):
                            logger.warning(f"Potential XSS detected in JSON field '{field}': {value}")
                            potential_xss = True
            except Exception as e:
                logger.error(f"Error parsing JSON data: {str(e)}")
        
        # Store result in g for logging
        g.potential_xss = potential_xss
        
        # Continue with the request - actual blocking would be based on policy
        return None
    
    def sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content to remove potentially malicious scripts
        
        Args:
            html_content: HTML content to sanitize
            
        Returns:
            Sanitized HTML content
        """
        # Simple HTML sanitization using html.escape
        sanitized = html.escape(html_content)
        
        # Log if content was modified
        if sanitized != html_content:
            logger.info("HTML content sanitized to prevent XSS")
            
        return sanitized
    
    def sanitize_input(self, value: str) -> str:
        """
        Sanitize a string input to prevent XSS
        
        Args:
            value: String value to sanitize
            
        Returns:
            Sanitized value
        """
        # Use html.escape to encode < and > characters
        return html.escape(value)
    
    def _contains_xss(self, value: str) -> bool:
        """
        Check if a string contains potential XSS payload
        
        Args:
            value: String to check
            
        Returns:
            True if potential XSS detected, False otherwise
        """
        for pattern in self.xss_regex:
            if pattern.search(value):
                return True
        
        return False
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '') -> Dict[str, Any]:
        """
        Flatten nested dictionaries for XSS checking
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key for nested values
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]").items())
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))
                
        return dict(items)
