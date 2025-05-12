"""
API Security Middleware

Provides middleware components for securing API endpoints.
Includes:
- JWT validation
- Rate limiting
- IP filtering
- Request sanitization
"""

import logging
import time
import re
from functools import wraps
from typing import Dict, Any, Optional, Callable, List, Union
import jwt
from flask import request, jsonify, g, Response
import ipaddress
import bleach
import json

from app.config.config_loader import config
from security.session_manager import session_manager

logger = logging.getLogger(__name__)

def validate_jwt(token: str) -> Dict[str, Any]:
    """
    Validate JWT token and extract payload
    
    Args:
        token: JWT token string
        
    Returns:
        Dict containing token payload if valid, or error information
    """
    try:
        # Get JWT secret from config
        jwt_secret = config.get('security.jwt_secret', '')
        jwt_algorithm = config.get('security.jwt_algorithm', 'HS256')
        
        if not jwt_secret:
            logger.error("JWT secret not configured")
            return {'valid': False, 'error': 'Token validation configuration error'}
        
        # Decode and validate token
        payload = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
        
        # Verify session is still valid
        if not session_manager.validate_session(payload.get('session_id', '')):
            return {'valid': False, 'error': 'Session has expired or been revoked'}
        
        return {'valid': True, 'payload': payload}
        
    except jwt.ExpiredSignatureError:
        return {'valid': False, 'error': 'Token has expired'}
    except jwt.InvalidTokenError:
        return {'valid': False, 'error': 'Invalid token'}
    except Exception as e:
        logger.error(f"Error validating JWT: {str(e)}")
        return {'valid': False, 'error': 'Token validation error'}

def jwt_required(f: Callable) -> Callable:
    """
    Decorator to require valid JWT token for route
    
    Usage:
    @app.route('/protected')
    @jwt_required
    def protected_route():
        return jsonify({"message": "This route is protected"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if token exists in Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header is missing'}), 401
        
        # Extract token from header (Bearer token format)
        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) < 2:
            return jsonify({'error': 'Invalid Authorization header format'}), 401
        
        token = parts[1]
        
        # Validate token
        result = validate_jwt(token)
        if not result['valid']:
            return jsonify({'error': result['error']}), 401
        
        # Store payload in request context for use in route
        g.jwt_payload = result['payload']
        
        # Continue to the route
        return f(*args, **kwargs)
    
    return decorated_function

class RateLimiter:
    """
    Rate limiting implementation for API endpoints
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RateLimiter, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize rate limiter"""
        self.requests = {}
        self.limits = {
            'default': {
                'requests': config.get('security.rate_limit.default.requests', 100),
                'window': config.get('security.rate_limit.default.window', 60),  # seconds
            },
            'auth': {
                'requests': config.get('security.rate_limit.auth.requests', 10),
                'window': config.get('security.rate_limit.auth.window', 60),
            },
            'sensitive': {
                'requests': config.get('security.rate_limit.sensitive.requests', 20),
                'window': config.get('security.rate_limit.sensitive.window', 60),
            }
        }
        
        # Set up regular cleanup of expired entries
        self.cleanup_interval = config.get('security.rate_limit.cleanup_interval', 300)  # 5 minutes
        self.last_cleanup = time.time()
    
    def get_client_identifier(self) -> str:
        """
        Get a unique identifier for the client
        
        Uses JWT subject if available, otherwise IP address
        """
        # Try to use JWT payload if available
        if hasattr(g, 'jwt_payload') and g.jwt_payload.get('sub'):
            return g.jwt_payload.get('sub')
        
        # Fallback to IP address
        return request.remote_addr
    
    def check_rate_limit(self, limit_type: str = 'default') -> Dict[str, Any]:
        """
        Check if request is within rate limits
        
        Args:
            limit_type: Type of rate limit to apply (default, auth, sensitive)
            
        Returns:
            Dict containing rate limit status
        """
        # Clean up expired entries if needed
        self._cleanup_if_needed()
        
        # Get client identifier
        client_id = self.get_client_identifier()
        
        # Get current time
        current_time = time.time()
        
        # Get limit configuration
        limit_config = self.limits.get(limit_type, self.limits['default'])
        max_requests = limit_config['requests']
        window = limit_config['window']
        
        # Initialize client entry if not exists
        if client_id not in self.requests:
            self.requests[client_id] = {}
        
        if limit_type not in self.requests[client_id]:
            self.requests[client_id][limit_type] = []
        
        # Get timestamps of previous requests
        client_requests = self.requests[client_id][limit_type]
        
        # Remove timestamps outside the time window
        window_start = current_time - window
        client_requests = [ts for ts in client_requests if ts > window_start]
        self.requests[client_id][limit_type] = client_requests
        
        # Check if limit is reached
        if len(client_requests) >= max_requests:
            return {
                'allowed': False,
                'limit': max_requests,
                'remaining': 0,
                'reset': window_start + window
            }
        
        # Add current timestamp to requests
        client_requests.append(current_time)
        
        # Return rate limit info
        return {
            'allowed': True,
            'limit': max_requests,
            'remaining': max_requests - len(client_requests),
            'reset': current_time + window
        }
    
    def _cleanup_if_needed(self):
        """Clean up expired entries if cleanup interval has passed"""
        current_time = time.time()
        if current_time - self.last_cleanup >= self.cleanup_interval:
            self._cleanup_expired()
            self.last_cleanup = current_time
    
    def _cleanup_expired(self):
        """Clean up expired rate limit entries"""
        current_time = time.time()
        
        for client_id in list(self.requests.keys()):
            for limit_type in list(self.requests[client_id].keys()):
                window = self.limits.get(limit_type, self.limits['default'])['window']
                window_start = current_time - window
                
                # Update request list to include only those within the time window
                self.requests[client_id][limit_type] = [
                    ts for ts in self.requests[client_id][limit_type] 
                    if ts > window_start
                ]
                
                # Remove the limit type entry if empty
                if not self.requests[client_id][limit_type]:
                    del self.requests[client_id][limit_type]
            
            # Remove the client entry if empty
            if not self.requests[client_id]:
                del self.requests[client_id]

def rate_limit(limit_type: str = 'default') -> Callable:
    """
    Decorator for rate limiting API endpoints
    
    Args:
        limit_type: Type of rate limit to apply (default, auth, sensitive)
        
    Usage:
    @app.route('/api/resource')
    @rate_limit('default')
    def get_resource():
        return jsonify({"data": "resource data"})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get rate limiter instance
            limiter = RateLimiter()
            
            # Check rate limit
            result = limiter.check_rate_limit(limit_type)
            
            # Set rate limit headers
            headers = {
                'X-RateLimit-Limit': str(result['limit']),
                'X-RateLimit-Remaining': str(result['remaining']),
                'X-RateLimit-Reset': str(int(result['reset']))
            }
            
            # Return 429 Too Many Requests if limit exceeded
            if not result['allowed']:
                response = jsonify({'error': 'Rate limit exceeded'})
                response.status_code = 429
                response.headers.extend(headers)
                return response
            
            # Continue to the route
            response = f(*args, **kwargs)
            
            # Add rate limit headers to response
            if isinstance(response, tuple):
                # Response is (json, status_code) or similar
                resp_obj = jsonify(response[0]) if not isinstance(response[0], Response) else response[0]
                resp_obj.headers.extend(headers)
                return (resp_obj, *response[1:])
            else:
                # Response is a response object
                if not isinstance(response, Response):
                    response = jsonify(response)
                response.headers.extend(headers)
                return response
        
        return decorated_function
    
    return decorator

def ip_whitelist(allowed_ips: Union[List[str], None] = None) -> Callable:
    """
    Decorator to restrict access to specific IP addresses
    
    Args:
        allowed_ips: List of allowed IP addresses or CIDR ranges, None to use config
        
    Usage:
    @app.route('/admin-only')
    @ip_whitelist(['192.168.1.1', '10.0.0.0/24'])
    def admin_only():
        return jsonify({"message": "Admin access granted"})
    """
    if allowed_ips is None:
        # Get allowed IPs from config
        allowed_ips = config.get('security.ip_whitelist', [])
    
    # Convert string IPs to networks
    networks = []
    for ip in allowed_ips:
        try:
            if '/' in ip:
                networks.append(ipaddress.ip_network(ip))
            else:
                networks.append(ipaddress.ip_network(f"{ip}/32"))
        except ValueError as e:
            logger.error(f"Invalid IP or CIDR in whitelist: {ip}, {str(e)}")
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.remote_addr
            
            # Check if IP is allowed
            try:
                client_ip_obj = ipaddress.ip_address(client_ip)
                allowed = any(client_ip_obj in network for network in networks)
                
                if not allowed:
                    logger.warning(f"IP whitelist blocked request from {client_ip}")
                    return jsonify({'error': 'Access denied'}), 403
                
                # IP is allowed, continue to route
                return f(*args, **kwargs)
                
            except ValueError:
                logger.error(f"Invalid client IP: {client_ip}")
                return jsonify({'error': 'Invalid client IP'}), 400
        
        return decorated_function
    
    return decorator

def sanitize_request(f: Callable) -> Callable:
    """
    Decorator to sanitize incoming request data
    
    Usage:
    @app.route('/api/post', methods=['POST'])
    @sanitize_request
    def create_post():
        # request.json is now sanitized
        return jsonify({"message": "Post created"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Sanitize request JSON data if present
        if request.is_json:
            # Get original JSON data
            original_data = request.get_json()
            
            # Sanitize data recursively
            sanitized_data = _sanitize_dict(original_data)
            
            # Replace request._cached_json to be accessed by request.get_json()
            if hasattr(request, '_cached_json'):
                request._cached_json = (sanitized_data, request._cached_json[1])
        
        # Sanitize form data if present
        if request.form:
            for key in request.form:
                if isinstance(request.form[key], str):
                    request.form._dict[key] = bleach.clean(request.form[key])
        
        # Continue to the route
        return f(*args, **kwargs)
    
    return decorated_function

def _sanitize_dict(data: Any) -> Any:
    """Recursively sanitize dictionary values"""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            sanitized[key] = _sanitize_dict(value)
        return sanitized
    elif isinstance(data, list):
        return [_sanitize_dict(item) for item in data]
    elif isinstance(data, str):
        # Clean HTML/dangerous content from strings
        return bleach.clean(data)
    else:
        # Return non-string values unchanged
        return data

# Create singleton instance
rate_limiter = RateLimiter()
