"""
Advanced Middleware Components for API Gateway
Rate limiting, authentication, logging, metrics, and circuit breaker middleware
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
import json
import asyncio
from typing import Dict, Any, Optional, Callable
import redis.asyncio as redis
from datetime import datetime, timedelta
import hashlib
import uuid
from contextlib import asynccontextmanager

from ..config import GatewayConfig, RateLimitConfig

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware with Redis backend
    Supports multiple rate limiting strategies and user-based limits
    """
    
    def __init__(self, app: ASGIApp, config: RateLimitConfig):
        super().__init__(app)
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, Dict[str, Any]] = {}
        
    async def init_redis(self):
        """Initialize Redis connection"""
        if self.config.enabled and not self.redis_client:
            try:
                self.redis_client = redis.from_url(
                    self.config.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                await self.redis_client.ping()
                logger.info("Redis connection established for rate limiting")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_client = None
    
    def get_rate_limit_key(self, request: Request, user_id: Optional[str] = None) -> str:
        """Generate rate limit key for the request"""
        # Use IP address as fallback
        client_ip = request.client.host if request.client else "unknown"
        
        # Use user ID if available, otherwise IP
        identifier = user_id or client_ip
        
        # Include endpoint and method
        endpoint = f"{request.method}:{request.url.path}"
        
        return f"rate_limit:{identifier}:{endpoint}"
    
    def parse_rate_limit(self, limit_str: str) -> tuple[int, int]:
        """Parse rate limit string like '100/minute' to (100, 60)"""
        try:
            count, period = limit_str.split('/')
            count = int(count)
            
            period_seconds = {
                'second': 1,
                'minute': 60,
                'hour': 3600,
                'day': 86400
            }.get(period, 60)
            
            return count, period_seconds
        except:
            return 100, 60  # Default: 100 per minute
    
    async def check_rate_limit(self, key: str, limit: int, window: int) -> tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limit"""
        current_time = int(time.time())
        window_start = current_time - window
        
        if self.redis_client:
            try:
                # Use Redis sliding window
                pipe = self.redis_client.pipeline()
                
                # Remove old entries
                pipe.zremrangebyscore(key, 0, window_start)
                
                # Count current requests
                pipe.zcard(key)
                
                # Add current request
                pipe.zadd(key, {str(uuid.uuid4()): current_time})
                
                # Set expiration
                pipe.expire(key, window)
                
                results = await pipe.execute()
                current_count = results[1]
                
                remaining = max(0, limit - current_count - 1)
                reset_time = current_time + window
                
                return current_count < limit, {
                    "limit": limit,
                    "remaining": remaining,
                    "reset": reset_time,
                    "reset_time": datetime.fromtimestamp(reset_time).isoformat()
                }
                
            except Exception as e:
                logger.error(f"Redis rate limit check failed: {e}")
                # Fallback to local cache
        
        # Local cache fallback
        if key not in self.local_cache:
            self.local_cache[key] = {"requests": [], "window": window}
        
        cache_entry = self.local_cache[key]
        
        # Remove old requests
        cache_entry["requests"] = [
            req_time for req_time in cache_entry["requests"] 
            if req_time > window_start
        ]
        
        current_count = len(cache_entry["requests"])
        
        if current_count < limit:
            cache_entry["requests"].append(current_time)
            remaining = limit - current_count - 1
        else:
            remaining = 0
        
        reset_time = current_time + window
        
        return current_count < limit, {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "reset_time": datetime.fromtimestamp(reset_time).isoformat()
        }
    
    def get_rate_limit_for_endpoint(self, request: Request, user_role: Optional[str] = None) -> str:
        """Get rate limit string for specific endpoint"""
        endpoint = f"{request.method} {request.url.path}"
        
        # Check for endpoint-specific limits
        from ..config import ENDPOINT_RATE_LIMITS
        if endpoint in ENDPOINT_RATE_LIMITS:
            return ENDPOINT_RATE_LIMITS[endpoint]
        
        # Check for role-based limits
        if user_role:
            role_limits = {
                "admin": self.config.admin_limit,
                "customer": self.config.customer_limit,
                "system": self.config.system_limit
            }
            if user_role in role_limits:
                return role_limits[user_role]
        
        # Default limits by endpoint type
        if "/auth/" in request.url.path:
            return self.config.auth_limit
        elif "/transactions" in request.url.path:
            return self.config.transaction_limit
        elif "/payments" in request.url.path:
            return self.config.payment_limit
        elif "/accounts" in request.url.path:
            return self.config.account_limit
        
        return self.config.default_limit
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through rate limiting"""
        if not self.config.enabled:
            return await call_next(request)
        
        # Initialize Redis if needed
        if not self.redis_client:
            await self.init_redis()
        
        # Skip rate limiting for certain paths
        if request.url.path in ["/health", "/metrics", "/docs", "/redoc"]:
            return await call_next(request)
        
        # Get user info from request if available
        user_id = getattr(request.state, "user_id", None)
        user_role = getattr(request.state, "user_role", None)
        
        # Get rate limit for this endpoint
        rate_limit_str = self.get_rate_limit_for_endpoint(request, user_role)
        limit, window = self.parse_rate_limit(rate_limit_str)
        
        # Generate rate limit key
        key = self.get_rate_limit_key(request, user_id)
        
        # Check rate limit
        allowed, info = await self.check_rate_limit(key, limit, window)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {key}: {info}")
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {limit} per {window} seconds",
                    "retry_after": info["reset"] - int(time.time())
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["reset"] - int(time.time()))
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Advanced request/response logging middleware
    """
    
    def __init__(self, app: ASGIApp, config: GatewayConfig):
        super().__init__(app)
        self.config = config
        self.logger = logging.getLogger("gateway.requests")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request and response details"""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        if self.config.log_requests:
            await self.log_request(request, request_id)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        if self.config.log_responses:
            await self.log_response(request, response, request_id, duration)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    async def log_request(self, request: Request, request_id: str):
        """Log incoming request details"""
        try:
            # Get user info if available
            user_id = getattr(request.state, "user_id", "anonymous")
            
            log_data = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "user_id": user_id,
                "content_type": request.headers.get("content-type"),
                "content_length": request.headers.get("content-length")
            }
            
            # Don't log sensitive headers
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            for header in sensitive_headers:
                if header in log_data["headers"]:
                    log_data["headers"][header] = "[REDACTED]"
            
            self.logger.info(f"REQUEST: {json.dumps(log_data)}")
            
        except Exception as e:
            self.logger.error(f"Error logging request: {e}")
    
    async def log_response(self, request: Request, response: Response, request_id: str, duration: float):
        """Log response details"""
        try:
            log_data = {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "response_headers": dict(response.headers),
                "content_type": response.headers.get("content-type")
            }
            
            # Log level based on status code
            if response.status_code >= 500:
                self.logger.error(f"RESPONSE: {json.dumps(log_data)}")
            elif response.status_code >= 400:
                self.logger.warning(f"RESPONSE: {json.dumps(log_data)}")
            else:
                self.logger.info(f"RESPONSE: {json.dumps(log_data)}")
                
        except Exception as e:
            self.logger.error(f"Error logging response: {e}")


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Metrics collection middleware for Prometheus
    """
    
    def __init__(self, app: ASGIApp, config: GatewayConfig):
        super().__init__(app)
        self.config = config
        self.metrics = {
            "requests_total": {},
            "request_duration": {},
            "requests_in_progress": 0,
            "errors_total": {}
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Collect metrics for the request"""
        if not self.config.monitoring.metrics_enabled:
            return await call_next(request)
        
        # Increment in-progress counter
        self.metrics["requests_in_progress"] += 1
        
        # Start timing
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            await self.record_metrics(request, response, start_time)
            
            return response
            
        except Exception as e:
            # Record error metrics
            await self.record_error_metrics(request, e, start_time)
            raise
        finally:
            # Decrement in-progress counter
            self.metrics["requests_in_progress"] -= 1
    
    async def record_metrics(self, request: Request, response: Response, start_time: float):
        """Record request metrics"""
        try:
            duration = time.time() - start_time
            method = request.method
            path = request.url.path
            status_code = response.status_code
            
            # Create metric labels
            labels = f"{method}:{path}:{status_code}"
            
            # Increment request counter
            if labels not in self.metrics["requests_total"]:
                self.metrics["requests_total"][labels] = 0
            self.metrics["requests_total"][labels] += 1
            
            # Record duration
            duration_key = f"{method}:{path}"
            if duration_key not in self.metrics["request_duration"]:
                self.metrics["request_duration"][duration_key] = []
            self.metrics["request_duration"][duration_key].append(duration)
            
            # Keep only last 1000 duration measurements
            if len(self.metrics["request_duration"][duration_key]) > 1000:
                self.metrics["request_duration"][duration_key] = \
                    self.metrics["request_duration"][duration_key][-1000:]
            
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
    
    async def record_error_metrics(self, request: Request, error: Exception, start_time: float):
        """Record error metrics"""
        try:
            method = request.method
            path = request.url.path
            error_type = type(error).__name__
            
            labels = f"{method}:{path}:{error_type}"
            
            if labels not in self.metrics["errors_total"]:
                self.metrics["errors_total"][labels] = 0
            self.metrics["errors_total"][labels] += 1
            
        except Exception as e:
            logger.error(f"Error recording error metrics: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        return {
            "requests_total": self.metrics["requests_total"].copy(),
            "request_duration": {
                k: {
                    "count": len(v),
                    "avg": sum(v) / len(v) if v else 0,
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0
                }
                for k, v in self.metrics["request_duration"].items()
            },
            "requests_in_progress": self.metrics["requests_in_progress"],
            "errors_total": self.metrics["errors_total"].copy()
        }


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """
    Circuit breaker middleware for service protection
    """
    
    def __init__(self, app: ASGIApp, config: GatewayConfig):
        super().__init__(app)
        self.config = config
        self.circuit_breakers = {}
    
    def get_circuit_breaker(self, service_name: str) -> Dict[str, Any]:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = {
                "state": "closed",  # closed, open, half_open
                "failure_count": 0,
                "last_failure_time": None,
                "success_count": 0,
                "total_requests": 0
            }
        return self.circuit_breakers[service_name]
    
    def should_allow_request(self, circuit_breaker: Dict[str, Any]) -> bool:
        """Check if request should be allowed through circuit breaker"""
        if not self.config.load_balancing.circuit_breaker_enabled:
            return True
        
        state = circuit_breaker["state"]
        
        if state == "closed":
            return True
        elif state == "open":
            # Check if recovery timeout has passed
            if circuit_breaker["last_failure_time"]:
                time_since_failure = time.time() - circuit_breaker["last_failure_time"]
                if time_since_failure >= self.config.load_balancing.recovery_timeout:
                    circuit_breaker["state"] = "half_open"
                    circuit_breaker["success_count"] = 0
                    return True
            return False
        elif state == "half_open":
            # Allow limited requests to test service recovery
            return circuit_breaker["success_count"] < 3
        
        return False
    
    def record_success(self, circuit_breaker: Dict[str, Any]):
        """Record successful request"""
        circuit_breaker["total_requests"] += 1
        
        if circuit_breaker["state"] == "half_open":
            circuit_breaker["success_count"] += 1
            if circuit_breaker["success_count"] >= 3:
                # Service recovered, close circuit
                circuit_breaker["state"] = "closed"
                circuit_breaker["failure_count"] = 0
        elif circuit_breaker["state"] == "closed":
            # Reset failure count on success
            circuit_breaker["failure_count"] = max(0, circuit_breaker["failure_count"] - 1)
    
    def record_failure(self, circuit_breaker: Dict[str, Any]):
        """Record failed request"""
        circuit_breaker["total_requests"] += 1
        circuit_breaker["failure_count"] += 1
        circuit_breaker["last_failure_time"] = time.time()
        
        # Check if threshold exceeded
        if circuit_breaker["failure_count"] >= self.config.load_balancing.failure_threshold:
            circuit_breaker["state"] = "open"
            logger.warning(f"Circuit breaker opened due to {circuit_breaker['failure_count']} failures")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through circuit breaker"""
        # Extract service name from request path
        path = request.url.path
        service_name = None
        
        # Map path to service
        from ..config import ROUTE_MAPPINGS
        for route_pattern, service in ROUTE_MAPPINGS.items():
            if route_pattern in path or path.startswith(route_pattern.split('{')[0]):
                service_name = service
                break
        
        if not service_name:
            return await call_next(request)
        
        # Get circuit breaker for service
        circuit_breaker = self.get_circuit_breaker(service_name)
        
        # Check if request should be allowed
        if not self.should_allow_request(circuit_breaker):
            logger.warning(f"Circuit breaker {service_name} is open, rejecting request")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Service temporarily unavailable",
                    "message": f"Circuit breaker for {service_name} is open",
                    "retry_after": self.config.load_balancing.recovery_timeout
                }
            )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record success or failure based on response
            if response.status_code < 500:
                self.record_success(circuit_breaker)
            else:
                self.record_failure(circuit_breaker)
            
            return response
            
        except Exception as e:
            # Record failure
            self.record_failure(circuit_breaker)
            raise
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        return {
            service: {
                "state": cb["state"],
                "failure_count": cb["failure_count"],
                "total_requests": cb["total_requests"],
                "last_failure_time": cb["last_failure_time"]
            }
            for service, cb in self.circuit_breakers.items()
        }


__all__ = [
    "RateLimitMiddleware",
    "LoggingMiddleware", 
    "MetricsMiddleware",
    "CircuitBreakerMiddleware"
]
