"""
API Gateway Security for Core Banking System

This module provides a secure API gateway layer to protect API endpoints
with authentication, authorization, rate limiting, and request validation.
"""

import time
import logging
import functools
import json
import re
from typing import Dict, List, Callable, Any, Optional, Union, Tuple
from flask import Flask, request, jsonify, g, Response

# Import security components
from security.auth import authenticate_user, verify_permissions
from security.access_control import check_access
from security.middleware.rate_limit import RateLimitMiddleware
from security.middleware.validation_middleware import RequestValidator
from security.middleware.xss_protection import XSSProtectionMiddleware
from security.logs.audit_logger import AuditLogger
from security.config import CORS_CONFIG

# Configure logger
logger = logging.getLogger(__name__)


class SecureAPIGateway:
    """Secure API Gateway for protecting API endpoints"""
    
    def __init__(self, app=None):
        """
        Initialize the secure API gateway
        
        Args:
            app: Flask application instance
        """
        self.app = app
        self.audit_logger = AuditLogger()
        self.protected_endpoints = {}
        self.global_middlewares = []
        
        # Initialize middleware components
        self.rate_limiter = RateLimitMiddleware()
        self.validator = RequestValidator()
        self.xss_protection = XSSProtectionMiddleware()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize the gateway with a Flask application
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Register error handlers
        app.register_error_handler(401, self._handle_unauthorized_error)
        app.register_error_handler(403, self._handle_forbidden_error)
        app.register_error_handler(429, self._handle_rate_limit_error)
        
        # Register global before request handler
        app.before_request(self._process_request)
        
        # Register global after request handler
        app.after_request(self._process_response)
        
        # Initialize middleware components
        self.rate_limiter.init_app(app)
        self.validator.init_app(app)
        self.xss_protection.init_app(app)
    
    def _process_request(self):
        """Process incoming request through security layers"""
        if request.path.startswith('/api/'):
            # Store request start time for logging
            g.request_start_time = time.time()
            g.request_id = self._generate_request_id()
            
            # Apply global middlewares
            for middleware in self.global_middlewares:
                result = middleware()
                if isinstance(result, Response):
                    return result
    
    def _process_response(self, response):
        """Process outgoing response with security headers"""
        if hasattr(g, 'request_start_time'):
            # Calculate request processing time
            processing_time = time.time() - g.request_start_time
            
            # Add security headers
            response = self._add_security_headers(response)
            
            # Log API request if it's an API endpoint
            if request.path.startswith('/api/'):
                self._log_api_request(request, response, processing_time)
        
        return response
    
    def _add_security_headers(self, response):
        """
        Add security headers to response
        
        Args:
            response: Flask response
            
        Returns:
            Flask response with security headers
        """
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    def _log_api_request(self, request, response, processing_time):
        """
        Log API request details
        
        Args:
            request: Flask request
            response: Flask response
            processing_time: Request processing time in seconds
        """
        # Extract basic request info
        request_info = {
            'request_id': getattr(g, 'request_id', None),
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': request.user_agent.string,
            'status_code': response.status_code,
            'processing_time_ms': round(processing_time * 1000, 2)
        }
        
        # Extract authenticated user if available
        if hasattr(g, 'user'):
            request_info['user_id'] = g.user.get('id')
            request_info['username'] = g.user.get('username')
        
        # Log API request
        logger.info(f"API Request: {json.dumps(request_info)}")
        
        # Log security events for failed authentication/authorization
        if response.status_code in (401, 403):
            self.audit_logger.log_event(
                event_type="security_violation",
                user_id=getattr(g, 'user', {}).get('id', 'anonymous'),
                description=f"Security violation: {response.status_code} response for {request.method} {request.path}",
                metadata=request_info
            )
    
    def _generate_request_id(self):
        """
        Generate a unique request ID
        
        Returns:
            str: Unique request ID
        """
        import uuid
        return str(uuid.uuid4())
    
    def _handle_unauthorized_error(self, error):
        """
        Handle 401 Unauthorized errors
        
        Args:
            error: Error object
            
        Returns:
            Response: JSON response with error details
        """
        response = jsonify({
            'status': 'error',
            'code': 401,
            'message': 'Authentication required'
        })
        response.status_code = 401
        return response
    
    def _handle_forbidden_error(self, error):
        """
        Handle 403 Forbidden errors
        
        Args:
            error: Error object
            
        Returns:
            Response: JSON response with error details
        """
        response = jsonify({
            'status': 'error',
            'code': 403,
            'message': 'Insufficient permissions'
        })
        response.status_code = 403
        return response
    
    def _handle_rate_limit_error(self, error):
        """
        Handle 429 Too Many Requests errors
        
        Args:
            error: Error object
            
        Returns:
            Response: JSON response with error details
        """
        response = jsonify({
            'status': 'error',
            'code': 429,
            'message': 'Rate limit exceeded',
            'retry_after': error.description.get('retry_after', 60)
        })
        response.status_code = 429
        return response
    
    def register_global_middleware(self, middleware_func: Callable):
        """
        Register a global middleware function
        
        Args:
            middleware_func: Middleware function to register
        """
        self.global_middlewares.append(middleware_func)
    
    def protect_endpoint(
        self, 
        endpoint: str, 
        methods: List[str] = None,
        roles: List[str] = None,
        rate_limit: str = None,
        schema: Dict = None
    ):
        """
        Decorator to protect API endpoints
        
        Args:
            endpoint: API endpoint path
            methods: HTTP methods to protect
            roles: Required roles for access
            rate_limit: Rate limit rule
            schema: Request validation schema
            
        Returns:
            Callable: Decorator function
        """
        methods = methods or ['GET', 'POST', 'PUT', 'DELETE']
        
        def decorator(f):
            @functools.wraps(f)
            def wrapped(*args, **kwargs):
                # Store endpoint configuration if not already stored
                if endpoint not in self.protected_endpoints:
                    self.protected_endpoints[endpoint] = {
                        'methods': methods,
                        'roles': roles,
                        'rate_limit': rate_limit,
                        'schema': schema
                    }
                
                # Step 1: Check authentication
                auth_header = request.headers.get('Authorization')
                if not auth_header:
                    return self._handle_unauthorized_error(None)
                
                # Extract and validate token
                try:
                    token_type, token = auth_header.split(' ', 1)
                    if token_type.lower() != 'bearer':
                        return self._handle_unauthorized_error(None)
                    
                    # Authenticate user with token
                    # This would call your JWT verification function
                    user = authenticate_user(token)
                    if not user:
                        return self._handle_unauthorized_error(None)
                    
                    # Store user in g for later use
                    g.user = user
                
                except Exception as e:
                    logger.error(f"Authentication error: {str(e)}")
                    return self._handle_unauthorized_error(None)
                
                # Step 2: Check authorization
                if roles:
                    has_permission = False
                    for role in roles:
                        if verify_permissions(user.get('id'), role):
                            has_permission = True
                            break
                    
                    if not has_permission:
                        return self._handle_forbidden_error(None)
                
                # Step 3: Check rate limit
                if rate_limit:
                    if self.rate_limiter.is_rate_limited(
                        request.remote_addr, 
                        f"{endpoint}:{request.method}", 
                        rate_limit
                    ):
                        return self._handle_rate_limit_error(None)
                
                # Step 4: Validate request schema
                if schema and request.method in ('POST', 'PUT'):
                    validation_result = self.validator.validate_request(request, schema)
                    if not validation_result['valid']:
                        return jsonify({
                            'status': 'error',
                            'code': 400,
                            'message': 'Invalid request data',
                            'errors': validation_result['errors']
                        }), 400
                
                # Step 5: Log access
                self.audit_logger.log_event(
                    event_type="api_access",
                    user_id=user.get('id'),
                    description=f"API access: {request.method} {endpoint}",
                    metadata={
                        'method': request.method,
                        'endpoint': endpoint,
                        'remote_addr': request.remote_addr,
                        'user_agent': request.user_agent.string
                    }
                )
                
                # All security checks passed, proceed to handler
                return f(*args, **kwargs)
            
            return wrapped
        
        return decorator


# Create singleton instance
api_gateway = SecureAPIGateway()

# Decorator for easy endpoint protection
protect_endpoint = api_gateway.protect_endpoint


# Example usage
if __name__ == "__main__":
    app = Flask(__name__)
    secure_api = SecureAPIGateway(app)
    
    @app.route('/api/protected-resource', methods=['GET'])
    @protect_endpoint('/api/protected-resource', roles=['admin'])
    def protected_resource():
        return jsonify({
            'status': 'success',
            'message': 'This is a protected resource',
            'data': {
                'user_id': g.user.get('id'),
                'username': g.user.get('username')
            }
        })
    
    app.run(debug=True)
