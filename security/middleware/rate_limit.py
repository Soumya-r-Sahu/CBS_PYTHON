"""
Rate Limiting Middleware for Core Banking System

This middleware implements rate limiting for API requests
to prevent abuse and ensure fair usage.
"""

import time
import logging
from functools import wraps
from flask import request, jsonify, g
from collections import defaultdict

# Configure logger
logger = logging.getLogger(__name__)

# In-memory storage for rate limiting
# In production, use Redis or another distributed storage
RATE_LIMIT_STORE = defaultdict(list)


def rate_limit(requests_per_minute=60):
    """
    Decorator to implement rate limiting per IP address.
    
    Args:
        requests_per_minute (int): Maximum requests allowed per minute
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            ip = request.remote_addr
            
            # Get current time
            current_time = time.time()
            
            # Clean up old requests (older than 1 minute)
            RATE_LIMIT_STORE[ip] = [t for t in RATE_LIMIT_STORE[ip] if current_time - t < 60]
            
            # Check if rate limit is exceeded
            if len(RATE_LIMIT_STORE[ip]) >= requests_per_minute:
                logger.warning(f"Rate limit exceeded for IP: {ip}")
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": "Too many requests, please try again later"
                }), 429
            
            # Add current request to the store
            RATE_LIMIT_STORE[ip].append(current_time)
            
            # Add rate limit headers to response
            remaining = requests_per_minute - len(RATE_LIMIT_STORE[ip])
            
            # Call the original function
            response = f(*args, **kwargs)
            
            # If response is a tuple (response, status_code), add headers to response[0]
            if isinstance(response, tuple):
                response[0].headers['X-RateLimit-Limit'] = str(requests_per_minute)
                response[0].headers['X-RateLimit-Remaining'] = str(remaining)
                response[0].headers['X-RateLimit-Reset'] = str(int(current_time + 60))
            else:
                response.headers['X-RateLimit-Limit'] = str(requests_per_minute)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(int(current_time + 60))
            
            return response
        
        return decorated_function
    
    return decorator
