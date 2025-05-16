"""
Rate limiting middleware for Mobile Banking API

Prevents abuse of the API by limiting request frequency
"""

from flask import Flask, request, jsonify
from functools import wraps
import time
import threading


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
# Simple in-memory rate limiter
# In production, use Redis or another distributed cache
class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.lock = threading.Lock()
        
        # Clean old requests periodically
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start a thread to clean up old request records"""
        def cleanup():
            while True:
                time.sleep(60)  # Clean every minute
                self._cleanup_old_requests()
                
        threading.Thread(target=cleanup, daemon=True).start()
    
    def _cleanup_old_requests(self):
        """Remove old request records"""
        current_time = time.time()
        with self.lock:
            for key in list(self.requests.keys()):
                # Remove entries older than 1 hour
                self.requests[key] = [
                    timestamp for timestamp in self.requests[key] 
                    if current_time - timestamp < 3600
                ]
                
                # Remove empty lists
                if not self.requests[key]:
                    del self.requests[key]
    
    def add_request(self, key, max_requests, time_window):
        """
        Add a request and check if rate limit is exceeded
        
        Args:
            key: Request identifier (e.g., IP address, user ID)
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
            
        Returns:
            bool: True if rate limit is exceeded, False otherwise
        """
        current_time = time.time()
        
        with self.lock:
            if key not in self.requests:
                self.requests[key] = []
                
            # Add current timestamp
            self.requests[key].append(current_time)
            
            # Filter recent requests within time window
            recent_requests = [
                timestamp for timestamp in self.requests[key] 
                if current_time - timestamp < time_window
            ]
            
            # Update with only recent requests
            self.requests[key] = recent_requests
            
            # Check if limit is exceeded
            return len(recent_requests) > max_requests

# Create a global rate limiter instance
rate_limiter = RateLimiter()

def setup_rate_limiting(app: Flask):
    """
    Set up rate limiting middleware
    
    Args:
        app: Flask application instance
    """
    # Nothing to initialize at the app level
    pass

def rate_limit(max_requests=100, time_window=60, key_func=None):
    """
    Decorator to apply rate limiting to routes
    
    Args:
        max_requests: Maximum number of requests allowed in the time window
        time_window: Time window in seconds
        key_func: Function to generate a key from the request (defaults to IP address)
        
    Usage:
        @rate_limit(max_requests=5, time_window=60)
        def login():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get key for rate limiting
            if key_func:
                key = key_func(request)
            else:
                key = request.remote_addr
            
            # Check rate limit
            if rate_limiter.add_request(key, max_requests, time_window):
                return jsonify({
                    'status': 'error',
                    'message': 'Rate limit exceeded',
                    'code': 'RATE_LIMIT_EXCEEDED'
                }), 429
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
