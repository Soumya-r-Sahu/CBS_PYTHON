"""
XSS Protection Middleware for Core Banking System

This middleware implements Cross-Site Scripting (XSS) protection
by sanitizing input and implementing Content Security Policy (CSP).
"""

import logging
import re
import html
from flask import request, g, current_app
from werkzeug.exceptions import BadRequest
from functools import wraps

# Configure logger
logger = logging.getLogger(__name__)


class XSSProtectionMiddleware:
    """Middleware for protecting against Cross-Site Scripting (XSS) attacks"""
    
    def __init__(self, app=None):
        """
        Initialize XSS protection middleware
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Regex patterns for detecting potential XSS attacks
        self.xss_patterns = [
            re.compile(r'<script.*?>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'on\w+\s*=', re.IGNORECASE),  # onClick, onLoad, etc.
            re.compile(r'data:\s*text/html', re.IGNORECASE),
            re.compile(r'expression\s*\(', re.IGNORECASE),
            re.compile(r'eval\s*\(', re.IGNORECASE),
        ]
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the middleware with a Flask application
        
        Args:
            app: Flask application instance
        """
        # Register XSS protection
        app.before_request(self._sanitize_input)
        app.after_request(self._add_csp_headers)
    
    def _sanitize_input(self):
        """Sanitize input data to prevent XSS attacks"""
        # Skip for safe HTTP methods
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return None
        
        # Check JSON data
        if request.is_json:
            json_data = request.get_json(silent=True)
            if json_data:
                self._check_json_data(json_data)
        
        # Check form data
        if request.form:
            for key, value in request.form.items():
                self._check_value(key, value)
        
        # Store sanitized request data
        g.sanitized_data = self._sanitize_request_data()
    
    def _check_json_data(self, data, path=""):
        """
        Recursively check JSON data for XSS patterns
        
        Args:
            data: JSON data to check
            path: Current path in the JSON structure for logging purposes
            
        Raises:
            BadRequest: If potential XSS is detected
        """
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                self._check_json_data(value, new_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                self._check_json_data(item, new_path)
        elif isinstance(data, str):
            self._check_value(path, data)
    
    def _check_value(self, key, value):
        """
        Check a single value for XSS patterns
        
        Args:
            key: Key or field name for the value
            value: Value to check
            
        Raises:
            BadRequest: If potential XSS is detected
        """
        if not isinstance(value, str):
            return
        
        for pattern in self.xss_patterns:
            if pattern.search(value):
                logger.warning(f"Potential XSS detected in field '{key}': {value[:50]}...")
                raise BadRequest("Invalid input detected")
    
    def _sanitize_request_data(self):
        """
        Create a sanitized copy of the request data
        
        Returns:
            dict: Sanitized request data
        """
        sanitized = {}
        
        # Handle JSON data
        if request.is_json:
            json_data = request.get_json(silent=True)
            if json_data:
                sanitized['json'] = self._sanitize_object(json_data)
        
        # Handle form data
        if request.form:
            sanitized['form'] = {}
            for key, value in request.form.items():
                sanitized['form'][key] = html.escape(value) if isinstance(value, str) else value
        
        return sanitized
    
    def _sanitize_object(self, obj):
        """
        Recursively sanitize an object (dict, list, etc.)
        
        Args:
            obj: Object to sanitize
            
        Returns:
            Sanitized object
        """
        if isinstance(obj, dict):
            return {k: self._sanitize_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_object(item) for item in obj]
        elif isinstance(obj, str):
            return html.escape(obj)
        else:
            return obj
    
    def _add_csp_headers(self, response):
        """
        Add Content Security Policy headers to response
        
        Args:
            response: Flask response object
            
        Returns:
            Modified response with CSP headers
        """
        # Basic CSP policy - customize according to your application's needs
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "object-src 'none'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # Enable XSS protection in browsers
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response


def xss_protected(f):
    """
    Decorator to apply XSS protection to a specific route
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Use sanitized data if available
        if hasattr(g, 'sanitized_data'):
            request.sanitized = g.sanitized_data
        
        return f(*args, **kwargs)
    
    return decorated_function


# Helper function to get sanitized request data
def get_sanitized_data():
    """
    Get sanitized request data
    
    Returns:
        dict: Sanitized request data or None if not available
    """
    return getattr(g, 'sanitized_data', None)
