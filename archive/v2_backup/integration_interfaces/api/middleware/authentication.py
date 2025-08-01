"""
Authentication Middleware for Mobile Banking API

Implements JWT-based authentication and authorization for API endpoints.
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, g
from functools import wraps
import jwt
from datetime import datetime, timedelta

# Add project root to path to enable imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import with fallback for backward compatibility
try:
    from utils.lib.encryption import verify_password
except ImportError:
    # Fallback to old import path
    try:
        from app.lib.encryption import verify_password
    except ImportError:
        # Simple fallback implementation
        import hashlib
        def verify_password(plain_password, hashed_password):
            """Simple fallback password verification"""
            return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

# Import configuration with fallback
try:
    from utils.config.api import get_api_config
except ImportError:
    # Define fallback
    def get_api_config():
        return {"secret_key": JWT_SECRET_KEY}

# Secret key should be stored in environment variables or secure config
JWT_SECRET_KEY = os.environ.get("CBS_JWT_SECRET", "your-secret-key-should-be-secure-and-in-env-variables")
JWT_EXPIRY_MINUTES = int(os.environ.get("CBS_JWT_EXPIRY", "60"))  # Token expiry time in minutes

def setup_auth_middleware(app: Flask):
    """
    Set up authentication middleware
    
    Args:
        app: Flask application instance
    """
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
    app.config['JWT_EXPIRY_MINUTES'] = JWT_EXPIRY_MINUTES

def token_required(f):
    """
    Decorator to validate JWT tokens for protected routes
    
    Usage:
        @token_required
        def protected_route():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in the header
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({
                'status': 'error',
                'message': 'Authentication token is missing',
                'code': 'MISSING_TOKEN'
            }), 401
        
        try:
            # Decode the token
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = {
                'customer_id': data['customer_id'],
                'device_id': data['device_id'],
                'role': data['role'],
                'exp': data['exp']
            }
            
            # Check if token has expired
            if datetime.utcfromtimestamp(data['exp']) < datetime.utcnow():
                return jsonify({
                    'status': 'error',
                    'message': 'Token has expired',
                    'code': 'TOKEN_EXPIRED'
                }), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'status': 'error',
                'message': 'Token has expired',
                'code': 'TOKEN_EXPIRED'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid token',
                'code': 'INVALID_TOKEN'
            }), 401
        
        # Pass the current user to the route
        return f(current_user, *args, **kwargs)
    
    return decorated

def generate_token(customer_id, device_id, role='customer'):
    """
    Generate a JWT token for the user
    
    Args:
        customer_id: Customer's unique identifier
        device_id: Device identifier
        role: User role (default: 'customer')
        
    Returns:
        str: JWT token
    """
    expiry = datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES)
    
    payload = {
        'customer_id': customer_id,
        'device_id': device_id,
        'role': role,
        'exp': expiry,
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    
    return token

def refresh_token(current_token):
    """
    Refresh JWT token before expiry
    
    Args:
        current_token: Current valid JWT token
        
    Returns:
        str: New JWT token
    """
    try:
        # Decode the current token
        data = jwt.decode(current_token, JWT_SECRET_KEY, algorithms=["HS256"])
        
        # Generate new token with same data but new expiry
        return generate_token(data['customer_id'], data['device_id'], data['role'])
    except jwt.InvalidTokenError:
        return None
