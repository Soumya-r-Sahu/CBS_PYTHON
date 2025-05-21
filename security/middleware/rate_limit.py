"""
Rate Limiting Middleware

This module provides rate limiting functionality to prevent abuse of API endpoints.
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple
from flask import Flask, request
from collections import defaultdict

# Configure logger
logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Rate limiting middleware for API requests
    
    This class tracks and limits the frequency of requests from specific sources
    to prevent API abuse.
    """
    
    def __init__(self):
        """Initialize the rate limiter"""
        self.request_logs = defaultdict(list)
        self.app = None
        
        # Default rate limit rules
        self.default_rules = {
            "1/second": 1,
            "5/minute": 5,
            "100/hour": 100,
            "1000/day": 1000
        }
    
    def init_app(self, app: Flask):
        """
        Initialize with Flask application
        
        Args:
            app: Flask application instance
        """
        self.app = app
    
    def is_rate_limited(self, client_id: str, resource: str, rule: str) -> bool:
        """
        Check if a client has exceeded rate limits for a resource
        
        Args:
            client_id: Identifier for the client (IP or user ID)
            resource: Resource being accessed (endpoint)
            rule: Rate limit rule (e.g., "5/minute")
            
        Returns:
            True if rate limited, False otherwise
        """
        now = time.time()
        key = f"{client_id}:{resource}"
        
        # Parse rate limit rule
        limit, window = self._parse_rule(rule)
        
        # Clean up old request logs
        self._clean_old_logs(key, now, window)
        
        # Check current request count against limit
        current_count = len(self.request_logs[key])
        
        # If under limit, add current request and allow
        if current_count < limit:
            self.request_logs[key].append(now)
            return False
        
        # Otherwise, rate limit is exceeded
        logger.warning(f"Rate limit exceeded for {client_id} on {resource} ({rule})")
        return True
    
    def get_reset_time(self, client_id: str, resource: str, rule: str) -> int:
        """
        Get time until rate limit resets
        
        Args:
            client_id: Identifier for the client
            resource: Resource being accessed
            rule: Rate limit rule
            
        Returns:
            Seconds until reset
        """
        now = time.time()
        key = f"{client_id}:{resource}"
        
        # Parse rate limit rule
        _, window = self._parse_rule(rule)
        
        # If no requests, reset time is 0
        if not self.request_logs[key]:
            return 0
        
        # Get oldest request time
        oldest = min(self.request_logs[key])
        
        # Calculate time until oldest request expires
        reset_time = max(0, int((oldest + window) - now))
        return reset_time
    
    def _parse_rule(self, rule: str) -> Tuple[int, int]:
        """
        Parse rate limit rule into limit and window
        
        Args:
            rule: Rate limit rule string (e.g., "5/minute")
            
        Returns:
            Tuple of (limit, window_seconds)
        """
        # Use default rule if provided rule not recognized
        if rule not in self.default_rules:
            parts = rule.split('/')
            if len(parts) != 2:
                logger.warning(f"Invalid rate limit rule: {rule}, using '5/minute'")
                return self._parse_rule("5/minute")
            
            try:
                limit = int(parts[0])
                
                # Parse time window
                window_unit = parts[1].lower()
                if window_unit == 'second' or window_unit == 'seconds':
                    window = 1
                elif window_unit == 'minute' or window_unit == 'minutes':
                    window = 60
                elif window_unit == 'hour' or window_unit == 'hours':
                    window = 3600
                elif window_unit == 'day' or window_unit == 'days':
                    window = 86400
                else:
                    logger.warning(f"Unknown time unit: {window_unit}, using minutes")
                    window = 60
                
                return limit, window
                
            except ValueError:
                logger.warning(f"Invalid rate limit: {rule}, using '5/minute'")
                return self._parse_rule("5/minute")
        
        # Handle predefined rules
        if rule == "1/second":
            return 1, 1
        elif rule == "5/minute":
            return 5, 60
        elif rule == "100/hour":
            return 100, 3600
        elif rule == "1000/day":
            return 1000, 86400
        else:
            # This should never happen given the check above
            return 5, 60
    
    def _clean_old_logs(self, key: str, now: float, window: int):
        """
        Remove expired request logs
        
        Args:
            key: Request log key
            now: Current timestamp
            window: Time window in seconds
        """
        # Keep only logs within the time window
        self.request_logs[key] = [
            timestamp for timestamp in self.request_logs[key]
            if now - timestamp < window
        ]
