"""
Enhanced Middleware Stack for CBS Platform V2.0 API Gateway
Comprehensive middleware with encryption, security, and monitoring capabilities.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
import ipaddress
import re

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import aioredis
import httpx

from .encryption_service import EndToEndEncryptionService

# Configure logging
logger = logging.getLogger(__name__)

class EncryptionMiddleware(BaseHTTPMiddleware):
    """
    Core encryption middleware that handles request/response encryption.
    """
    
    def __init__(self, app, encryption_service: EndToEndEncryptionService, config: Dict[str, Any]):
        super().__init__(app)
        self.encryption_service = encryption_service
        self.config = config
        self.enabled = config.get("enabled", True)
        self.enforce_encryption = config.get("enforce_encryption", False)
        self.encrypted_routes = config.get("encrypted_routes", [])
        self.bypass_routes = config.get("bypass_routes", ["/health", "/docs", "/openapi.json"])
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Process request with encryption handling."""
        
        # Skip encryption for bypass routes
        if any(request.url.path.startswith(route) for route in self.bypass_routes):
            return await call_next(request)
        
        # Check if encryption is required for this route
        encryption_required = (
            self.enforce_encryption or 
            any(request.url.path.startswith(route) for route in self.encrypted_routes)
        )
        
        # Handle encrypted requests
        if self.enabled and request.headers.get("X-Encryption-Enabled") == "true":
            try:
                # Store original body for decryption
                body = await request.body()
                if body:
                    key_id = request.headers.get("X-Encryption-Key-Id")
                    if key_id:
                        decrypted_body = await self.encryption_service.decrypt_request_body(body, key_id)
                        # Replace request body with decrypted content
                        request._body = decrypted_body.encode()
                
                # Add encryption flag to request state
                request.state.encryption_enabled = True
                
            except Exception as e:
                logger.error(f"Request decryption failed: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Request decryption failed", "code": "ENCRYPTION_ERROR"}
                )
        
        elif encryption_required:
            # Encryption is required but not provided
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Encryption required for this endpoint", "code": "ENCRYPTION_REQUIRED"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Handle encrypted responses
        if (self.enabled and 
            hasattr(request.state, 'encryption_enabled') and 
            request.state.encryption_enabled and
            response.status_code < 400):
            
            try:
                # Extract response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                if response_body:
                    # Parse and encrypt response
                    response_data = json.loads(response_body.decode())
                    encrypted_response = await self.encryption_service.encrypt_response(response_data)
                    
                    # Create new response with encrypted content
                    response = JSONResponse(
                        content=encrypted_response,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
                    response.headers["X-Encryption-Enabled"] = "true"
                    response.headers["X-Encryption-Key-Id"] = await self.encryption_service.get_current_key_id()
            
            except Exception as e:
                logger.error(f"Response encryption failed: {str(e)}")
                # Return original response if encryption fails
                pass
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds comprehensive security headers to all responses.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
            "X-Permitted-Cross-Domain-Policies": "none",
            "X-Download-Options": "noopen",
            "X-DNS-Prefetch-Control": "off"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # Add unique request ID
        response.headers["X-Request-ID"] = str(uuid.uuid4())
        
        # Remove server information headers
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting with encryption-aware features.
    """
    
    def __init__(self, app, config: Dict[str, Any], encryption_service: EndToEndEncryptionService):
        super().__init__(app)
        self.config = config
        self.encryption_service = encryption_service
        self.enabled = config.get("enabled", True)
        self.default_rate = config.get("default_rate", 100)  # requests per minute
        self.default_burst = config.get("burst_size", 20)
        self.window_size = config.get("window_size", 60)  # seconds
        self.storage = {}  # In-memory storage (use Redis in production)
        self.route_limits = config.get("route_limits", {})
        self.encrypted_bonus = config.get("encrypted_bonus", 1.5)  # Higher limits for encrypted requests
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Apply rate limiting logic."""
        
        if not self.enabled:
            return await call_next(request)
        
        # Determine rate limit key
        client_ip = request.client.host
        user_id = getattr(request.state, 'user_id', None)
        rate_key = f"rate_limit:{user_id or client_ip}:{request.url.path}"
        
        # Get rate limit for this route
        route_limit = self._get_route_limit(request.url.path)
        
        # Apply encrypted request bonus
        if hasattr(request.state, 'encryption_enabled') and request.state.encryption_enabled:
            route_limit = int(route_limit * self.encrypted_bonus)
        
        # Check rate limit
        if await self._is_rate_limited(rate_key, route_limit):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": self.window_size
                },
                headers={"Retry-After": str(self.window_size)}
            )
        
        # Update rate limit counter
        await self._update_rate_limit(rate_key)
        
        return await call_next(request)
    
    def _get_route_limit(self, path: str) -> int:
        """Get rate limit for a specific route."""
        for route_pattern, limit in self.route_limits.items():
            if re.match(route_pattern, path):
                return limit
        return self.default_rate
    
    async def _is_rate_limited(self, key: str, limit: int) -> bool:
        """Check if request should be rate limited."""
        current_time = time.time()
        window_start = current_time - self.window_size
        
        # Clean old entries
        if key in self.storage:
            self.storage[key] = [
                timestamp for timestamp in self.storage[key] 
                if timestamp > window_start
            ]
        else:
            self.storage[key] = []
        
        return len(self.storage[key]) >= limit
    
    async def _update_rate_limit(self, key: str):
        """Update rate limit counter."""
        current_time = time.time()
        if key not in self.storage:
            self.storage[key] = []
        self.storage[key].append(current_time)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware with encryption support.
    """
    
    def __init__(self, app, auth_service, encryption_service: EndToEndEncryptionService, 
                 public_routes: List[str], admin_routes: List[str]):
        super().__init__(app)
        self.auth_service = auth_service
        self.encryption_service = encryption_service
        self.public_routes = public_routes
        self.admin_routes = admin_routes
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Authenticate requests with encryption support."""
        
        # Skip authentication for public routes
        if any(request.url.path.startswith(route) for route in self.public_routes):
            return await call_next(request)
        
        # Extract authentication token
        auth_header = request.headers.get("Authorization")
        api_key = request.headers.get("X-API-Key")
        
        if not auth_header and not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Authentication required", "code": "AUTH_REQUIRED"}
            )
        
        try:
            # Verify token/API key
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                token_data = await self.auth_service.verify_encrypted_token(token)
            elif api_key:
                token_data = await self.auth_service.verify_api_key(api_key)
            else:
                raise ValueError("Invalid authentication format")
            
            # Add user info to request state
            request.state.user_id = token_data.user_id
            request.state.username = token_data.username
            request.state.roles = token_data.roles
            request.state.permissions = token_data.permissions
            
            # Check admin access for admin routes
            if any(request.url.path.startswith(route) for route in self.admin_routes):
                if not self._has_admin_access(token_data):
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"error": "Admin access required", "code": "ADMIN_ACCESS_REQUIRED"}
                    )
            
            return await call_next(request)
        
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Authentication failed", "code": "AUTH_FAILED"}
            )
    
    def _has_admin_access(self, token_data) -> bool:
        """Check if user has admin access."""
        user_roles = getattr(token_data, 'roles', [])
        admin_permissions = getattr(token_data, 'permissions', [])
        
        return (
            'admin' in user_roles or
            'super_admin' in user_roles or
            'admin:system' in admin_permissions
        )


class CacheMiddleware(BaseHTTPMiddleware):
    """
    Caching middleware with encryption-aware caching.
    """
    
    def __init__(self, app, config: Dict[str, Any], encryption_service: EndToEndEncryptionService):
        super().__init__(app)
        self.config = config
        self.encryption_service = encryption_service
        self.enabled = config.get("enabled", True)
        self.ttl = config.get("ttl", 300)  # 5 minutes
        self.cache = {}  # In-memory cache (use Redis in production)
        self.cacheable_methods = config.get("cacheable_methods", ["GET"])
        self.cacheable_routes = config.get("cacheable_routes", [])
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Apply caching logic."""
        
        if not self.enabled or request.method not in self.cacheable_methods:
            return await call_next(request)
        
        # Check if route is cacheable
        if not any(request.url.path.startswith(route) for route in self.cacheable_routes):
            return await call_next(request)
        
        # Generate cache key
        cache_key = await self._generate_cache_key(request)
        
        # Check cache
        cached_response = await self._get_cached_response(cache_key)
        if cached_response:
            return JSONResponse(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response.get("headers", {})
            )
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            await self._cache_response(cache_key, response)
        
        return response
    
    async def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        user_id = getattr(request.state, 'user_id', 'anonymous')
        query_params = str(request.query_params)
        
        # Include encryption state in cache key
        encryption_state = "encrypted" if hasattr(request.state, 'encryption_enabled') else "plain"
        
        key_data = f"{request.method}:{request.url.path}:{query_params}:{user_id}:{encryption_state}"
        return f"cache:{hash(key_data)}"
    
    async def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response."""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if cached_data["expires"] > time.time():
                return cached_data
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        return None
    
    async def _cache_response(self, cache_key: str, response: StarletteResponse):
        """Cache response."""
        try:
            # Extract response content
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            if response_body:
                content = json.loads(response_body.decode())
                
                # Store in cache
                self.cache[cache_key] = {
                    "content": content,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "expires": time.time() + self.ttl
                }
        
        except Exception as e:
            logger.error(f"Failed to cache response: {str(e)}")


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Audit middleware for compliance and security monitoring.
    """
    
    def __init__(self, app, event_bus, encryption_service: EndToEndEncryptionService):
        super().__init__(app)
        self.event_bus = event_bus
        self.encryption_service = encryption_service
        self.audit_routes = ["/api/v1/payments", "/api/v1/transactions", "/api/v1/accounts"]
        self.sensitive_fields = ["password", "pin", "card_number", "cvv", "ssn", "tax_id"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Audit request and response."""
        
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Check if this request needs auditing
        needs_audit = any(request.url.path.startswith(route) for route in self.audit_routes)
        
        if needs_audit:
            # Log request
            await self._log_request(request, request_id)
        
        # Process request
        response = await call_next(request)
        
        if needs_audit:
            # Log response
            processing_time = time.time() - start_time
            await self._log_response(request, response, request_id, processing_time)
        
        return response
    
    async def _log_request(self, request: Request, request_id: str):
        """Log audit request."""
        try:
            # Extract safe request data
            audit_data = {
                "event_type": "api_request",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host,
                "user_agent": request.headers.get("User-Agent", ""),
                "user_id": getattr(request.state, 'user_id', None),
                "username": getattr(request.state, 'username', None),
                "encrypted": hasattr(request.state, 'encryption_enabled'),
                "query_params": dict(request.query_params)
            }
            
            # Extract body for specific routes (without sensitive data)
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        body_data = json.loads(body.decode())
                        # Remove sensitive fields
                        sanitized_body = self._sanitize_data(body_data)
                        audit_data["request_body"] = sanitized_body
                except Exception:
                    pass
            
            # Encrypt audit data
            encrypted_audit = await self.encryption_service.encrypt_sensitive_data(audit_data)
            
            # Send to event bus
            await self.event_bus.publish("audit.request", encrypted_audit)
        
        except Exception as e:
            logger.error(f"Failed to log audit request: {str(e)}")
    
    async def _log_response(self, request: Request, response: StarletteResponse, 
                           request_id: str, processing_time: float):
        """Log audit response."""
        try:
            audit_data = {
                "event_type": "api_response",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": response.status_code,
                "processing_time_ms": round(processing_time * 1000, 2),
                "response_size": len(response.body) if hasattr(response, 'body') else 0,
                "user_id": getattr(request.state, 'user_id', None)
            }
            
            # Log errors and security events
            if response.status_code >= 400:
                audit_data["error"] = True
                audit_data["error_type"] = "client_error" if response.status_code < 500 else "server_error"
            
            # Encrypt audit data
            encrypted_audit = await self.encryption_service.encrypt_sensitive_data(audit_data)
            
            # Send to event bus
            await self.event_bus.publish("audit.response", encrypted_audit)
        
        except Exception as e:
            logger.error(f"Failed to log audit response: {str(e)}")
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive fields from data."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if key.lower() in self.sensitive_fields:
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, dict):
                    sanitized[key] = self._sanitize_data(value)
                elif isinstance(value, list):
                    sanitized[key] = [self._sanitize_data(item) if isinstance(item, dict) else item for item in value]
                else:
                    sanitized[key] = value
            return sanitized
        return data


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """
    Circuit breaker middleware for service resilience.
    """
    
    def __init__(self, app, config: Dict[str, Any], service_router):
        super().__init__(app)
        self.config = config
        self.service_router = service_router
        self.enabled = config.get("enabled", True)
        self.failure_threshold = config.get("failure_threshold", 5)
        self.recovery_timeout = config.get("recovery_timeout", 60)
        self.circuit_states = {}  # service_name -> state
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Apply circuit breaker logic."""
        
        if not self.enabled:
            return await call_next(request)
        
        # Determine target service from path
        service_name = self._get_service_name(request.url.path)
        
        if service_name:
            # Check circuit state
            circuit_state = self._get_circuit_state(service_name)
            
            if circuit_state == "open":
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={
                        "error": "Service temporarily unavailable",
                        "code": "CIRCUIT_BREAKER_OPEN",
                        "service": service_name
                    }
                )
            
            # Process request
            try:
                response = await call_next(request)
                
                # Record success
                if response.status_code < 500:
                    self._record_success(service_name)
                else:
                    self._record_failure(service_name)
                
                return response
            
            except Exception as e:
                self._record_failure(service_name)
                raise
        
        return await call_next(request)
    
    def _get_service_name(self, path: str) -> Optional[str]:
        """Extract service name from request path."""
        service_mapping = {
            "/api/v1/accounts": "account-service",
            "/api/v1/customers": "customer-service",
            "/api/v1/payments": "payment-service",
            "/api/v1/transactions": "transaction-service",
            "/api/v1/loans": "loan-service",
            "/api/v1/notifications": "notification-service",
            "/api/v1/audit": "audit-service"
        }
        
        for route, service in service_mapping.items():
            if path.startswith(route):
                return service
        return None
    
    def _get_circuit_state(self, service_name: str) -> str:
        """Get circuit breaker state for service."""
        if service_name not in self.circuit_states:
            self.circuit_states[service_name] = {
                "state": "closed",
                "failures": 0,
                "last_failure": None
            }
        
        circuit = self.circuit_states[service_name]
        
        # Check if circuit should be closed after recovery timeout
        if (circuit["state"] == "open" and 
            circuit["last_failure"] and
            time.time() - circuit["last_failure"] > self.recovery_timeout):
            circuit["state"] = "half-open"
            circuit["failures"] = 0
        
        return circuit["state"]
    
    def _record_success(self, service_name: str):
        """Record successful request."""
        if service_name in self.circuit_states:
            circuit = self.circuit_states[service_name]
            circuit["failures"] = 0
            circuit["state"] = "closed"
    
    def _record_failure(self, service_name: str):
        """Record failed request."""
        if service_name not in self.circuit_states:
            self.circuit_states[service_name] = {
                "state": "closed",
                "failures": 0,
                "last_failure": None
            }
        
        circuit = self.circuit_states[service_name]
        circuit["failures"] += 1
        circuit["last_failure"] = time.time()
        
        # Open circuit if failure threshold reached
        if circuit["failures"] >= self.failure_threshold:
            circuit["state"] = "open"
            logger.warning(f"Circuit breaker opened for {service_name}")


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Metrics collection middleware for monitoring.
    """
    
    def __init__(self, app, config: Dict[str, Any]):
        super().__init__(app)
        self.config = config
        self.enabled = config.get("enabled", True)
        self.metrics = {
            "requests_total": 0,
            "requests_by_status": {},
            "requests_by_method": {},
            "requests_by_path": {},
            "response_time_sum": 0,
            "response_time_count": 0,
            "encrypted_requests": 0,
            "errors_total": 0
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Collect metrics."""
        
        if not self.enabled:
            return await call_next(request)
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Collect metrics
        processing_time = time.time() - start_time
        
        self.metrics["requests_total"] += 1
        self.metrics["response_time_sum"] += processing_time
        self.metrics["response_time_count"] += 1
        
        # Status code metrics
        status_code = response.status_code
        self.metrics["requests_by_status"][status_code] = self.metrics["requests_by_status"].get(status_code, 0) + 1
        
        # Method metrics
        method = request.method
        self.metrics["requests_by_method"][method] = self.metrics["requests_by_method"].get(method, 0) + 1
        
        # Path metrics
        path = request.url.path
        self.metrics["requests_by_path"][path] = self.metrics["requests_by_path"].get(path, 0) + 1
        
        # Encryption metrics
        if hasattr(request.state, 'encryption_enabled'):
            self.metrics["encrypted_requests"] += 1
        
        # Error metrics
        if status_code >= 400:
            self.metrics["errors_total"] += 1
        
        return response
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        avg_response_time = (
            self.metrics["response_time_sum"] / self.metrics["response_time_count"]
            if self.metrics["response_time_count"] > 0 else 0
        )
        
        return {
            **self.metrics,
            "avg_response_time": avg_response_time,
            "timestamp": datetime.utcnow().isoformat()
        }


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive logging middleware with encryption awareness.
    """
    
    def __init__(self, app, config: Dict[str, Any], event_bus, encryption_service: EndToEndEncryptionService):
        super().__init__(app)
        self.config = config
        self.event_bus = event_bus
        self.encryption_service = encryption_service
        self.enabled = config.get("enabled", True)
        self.log_level = config.get("log_level", "INFO")
        self.log_requests = config.get("log_requests", True)
        self.log_responses = config.get("log_responses", True)
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Log request and response."""
        
        if not self.enabled:
            return await call_next(request)
        
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Log request
        if self.log_requests:
            await self._log_request(request, request_id)
        
        # Process request
        response = await call_next(request)
        
        # Log response
        if self.log_responses:
            processing_time = time.time() - start_time
            await self._log_response(request, response, request_id, processing_time)
        
        return response
    
    async def _log_request(self, request: Request, request_id: str):
        """Log request details."""
        try:
            log_data = {
                "event_type": "request",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("User-Agent", ""),
                "encrypted": hasattr(request.state, 'encryption_enabled'),
                "user_id": getattr(request.state, 'user_id', None)
            }
            
            logger.info(f"Request: {json.dumps(log_data, separators=(',', ':'))}")
            
            # Send to event bus
            await self.event_bus.publish("logging.request", log_data)
        
        except Exception as e:
            logger.error(f"Failed to log request: {str(e)}")
    
    async def _log_response(self, request: Request, response: StarletteResponse, 
                           request_id: str, processing_time: float):
        """Log response details."""
        try:
            log_data = {
                "event_type": "response",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": response.status_code,
                "processing_time_ms": round(processing_time * 1000, 2),
                "response_size": len(response.body) if hasattr(response, 'body') else 0
            }
            
            # Log level based on status code
            if response.status_code >= 500:
                logger.error(f"Response: {json.dumps(log_data, separators=(',', ':'))}")
            elif response.status_code >= 400:
                logger.warning(f"Response: {json.dumps(log_data, separators=(',', ':'))}")
            else:
                logger.info(f"Response: {json.dumps(log_data, separators=(',', ':'))}")
            
            # Send to event bus
            await self.event_bus.publish("logging.response", log_data)
        
        except Exception as e:
            logger.error(f"Failed to log response: {str(e)}")


# Export all middleware classes
__all__ = [
    "EncryptionMiddleware",
    "SecurityHeadersMiddleware", 
    "RateLimitMiddleware",
    "AuthenticationMiddleware",
    "CacheMiddleware",
    "AuditMiddleware",
    "CircuitBreakerMiddleware",
    "MetricsMiddleware",
    "LoggingMiddleware"
]
