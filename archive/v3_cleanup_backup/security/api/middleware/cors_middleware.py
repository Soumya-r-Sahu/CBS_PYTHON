"""
CORS Middleware for Core Banking System

This middleware implements Cross-Origin Resource Sharing (CORS) protection
to control which domains can access the API and what methods they can use.
"""

import logging
from flask import request, current_app
from functools import wraps

# Import configuration
try:
    # Try to import from the new compatibility module
    from utils.config.compatibility import get_cors_settings
    CORS_CONFIG = get_cors_settings()
except ImportError:
    try:
        # Fall back to old import path
        from security.config import CORS_CONFIG
    except ImportError:
        # Default fallback configuration
        CORS_CONFIG = {
            "allowed_origins": ["*"],
            "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allowed_headers": ["Authorization", "Content-Type", "Accept", "Origin"],
            "expose_headers": [],
            "supports_credentials": True,
            "max_age": 3600
        }

# Configure logger
logger = logging.getLogger(__name__)


class CORSMiddleware:
    """Middleware for handling Cross-Origin Resource Sharing (CORS)"""
    
    def __init__(self, app=None):
        """
        Initialize CORS middleware
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the middleware with a Flask application
        
        Args:
            app: Flask application instance
        """
        # Register CORS handling functions
        app.before_request(self._handle_cors_preflight)
        app.after_request(self._add_cors_headers)
    
    def _handle_cors_preflight(self):
        """Handle CORS preflight (OPTIONS) requests"""
        if request.method != 'OPTIONS':
            return None
        
        # Check if origin is allowed
        origin = request.headers.get('Origin')
        allowed_origins = CORS_CONFIG["allowed_origins"]
        
        # If we have wildcard origin or the specific origin is allowed
        if '*' in allowed_origins or origin in allowed_origins:
            response = current_app.make_default_options_response()
            return response
        
        # Log and deny unallowed origins for preflight
        logger.warning(f"CORS preflight denied for origin: {origin}")
        return {'error': 'CORS not allowed'}, 403
    
    def _add_cors_headers(self, response):
        """
        Add CORS headers to response
        
        Args:
            response: Flask response object
            
        Returns:
            Modified response with CORS headers
        """
        origin = request.headers.get('Origin')
        allowed_origins = CORS_CONFIG["allowed_origins"]
        
        # Only set CORS headers if the origin is allowed
        if '*' in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = '*'
        elif origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            # Don't set CORS headers for disallowed origins
            return response
        
        # Set allowed methods
        response.headers['Access-Control-Allow-Methods'] = ', '.join(CORS_CONFIG["allowed_methods"])
        
        # Set allowed headers
        response.headers['Access-Control-Allow-Headers'] = ', '.join(CORS_CONFIG["allowed_headers"])
        
        # Set exposed headers
        if CORS_CONFIG.get("expose_headers"):
            response.headers['Access-Control-Expose-Headers'] = ', '.join(CORS_CONFIG["expose_headers"])
        
        # Set credentials support
        if CORS_CONFIG.get("supports_credentials"):
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Set max age for preflight cache
        if CORS_CONFIG.get("max_age"):
            response.headers['Access-Control-Max-Age'] = str(CORS_CONFIG["max_age"])
        
        return response


def cors_protected(allowed_origins=None):
    """
    Decorator to protect a specific route with custom CORS settings
    
    Args:
        allowed_origins: List of origins allowed for this specific route
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            origin = request.headers.get('Origin')
            
            # Use route-specific allowed origins if provided, otherwise use global config
            origins_to_check = allowed_origins or CORS_CONFIG["allowed_origins"]
            
            if '*' in origins_to_check or origin in origins_to_check:
                # Origin is allowed, proceed with the request
                return f(*args, **kwargs)
            else:
                # Origin is not allowed, deny access
                logger.warning(f"CORS access denied for origin {origin} to route {request.path}")
                return {'error': 'Cross-origin request denied'}, 403
        
        return wrapped
    
    return decorator
