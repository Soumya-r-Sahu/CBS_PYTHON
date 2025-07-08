"""
Authentication Middleware for Core Banking System

This middleware handles authentication for web requests,
validating JWT tokens and attaching user information to the request.
"""

import logging
from functools import wraps
from flask import request, jsonify, g
from security.auth import verify_auth_token

# Configure logger
logger = logging.getLogger(__name__)


def auth_middleware():
    """
    Authentication middleware for Flask.
    Validates JWT token from the Authorization header and attaches user info to request.
    """
    # Extract token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.warning("Missing or invalid Authorization header")
        return jsonify({"error": "Unauthorized - Missing or invalid token"}), 401
    
    # Extract the token
    token = auth_header.split(' ')[1]
    
    # Verify token
    token_data = verify_auth_token(token)
    if not token_data:
        logger.warning("Invalid or expired token")
        return jsonify({"error": "Unauthorized - Invalid or expired token"}), 401
    
    # Attach user info to Flask's g object for use in route handlers
    g.user = token_data
    
    # Allow the request to proceed
    return None


def require_auth(f):
    """
    Decorator for routes that require authentication.
    
    Args:
        f: The function to wrap
        
    Returns:
        The wrapped function
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Apply auth middleware
        result = auth_middleware()
        if result:
            # Auth failed, return the error response
            return result
        
        # Auth succeeded, call the original function
        return f(*args, **kwargs)
    
    return decorated


def require_role(required_role):
    """
    Decorator for routes that require a specific role.
    
    Args:
        required_role (str): The role required to access the route
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Apply auth middleware
            result = auth_middleware()
            if result:
                # Auth failed, return the error response
                return result
            
            # Check if user has the required role
            user_role = g.user.get('role')
            if user_role != required_role and user_role != 'admin':
                logger.warning(f"Access denied: User {g.user.get('username')} with role {user_role} attempted to access endpoint requiring role {required_role}")
                return jsonify({"error": f"Forbidden - Requires {required_role} role"}), 403
            
            # User has required role, call the original function
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
