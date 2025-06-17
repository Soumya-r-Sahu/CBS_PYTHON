"""
Advanced API Gateway for CBS_PYTHON V2.0

This module implements a comprehensive API Gateway with:
- Advanced authentication (OAuth2, JWT, API Keys)
- Dynamic rate limiting and throttling
- Request/response transformation
- API versioning
- Circuit breakers and retry logic
- Real-time monitoring and metrics
- GraphQL support
- Webhook management
"""

import asyncio
import json
import time
import logging
import traceback
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import hmac
import jwt
import redis
import aioredis
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import httpx
from circuitbreaker import circuit
import graphene
from graphql.execution.executors.asyncio import AsyncioExecutor
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import pydantic
from pydantic import BaseModel, Field, validator
import kafka
from kafka import KafkaProducer
import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)

# Prometheus metrics
request_count = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('api_request_duration_seconds', 'API request duration')
active_connections = Gauge('api_active_connections', 'Active API connections')
rate_limit_hits = Counter('api_rate_limit_hits_total', 'Rate limit hits', ['endpoint'])
circuit_breaker_trips = Counter('api_circuit_breaker_trips_total', 'Circuit breaker trips', ['service'])


class APIVersion(str, Enum):
    """API version enumeration"""
    V1 = "v1"
    V2 = "v2"


class AuthMethod(str, Enum):
    """Authentication method enumeration"""
    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"


class RateLimitStrategy(str, Enum):
    """Rate limiting strategy enumeration"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class APIEndpointConfig:
    """Configuration for API endpoint"""
    path: str
    methods: List[str]
    auth_required: bool = True
    auth_methods: List[AuthMethod] = None
    rate_limit: Optional[int] = None
    rate_limit_window: int = 60  # seconds
    rate_limit_strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    roles_required: List[str] = None
    permissions_required: List[str] = None
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    cache_ttl: Optional[int] = None
    request_size_limit: Optional[int] = None
    response_transform: Optional[Dict] = None
    webhook_events: List[str] = None
    enabled: bool = True
    deprecated: bool = False
    version_introduced: APIVersion = APIVersion.V2
    documentation: str = ""


@dataclass
class ServiceConfig:
    """Microservice configuration"""
    name: str
    base_url: str
    health_endpoint: str = "/health"
    timeout: int = 30
    retries: int = 3
    circuit_breaker_enabled: bool = True
    load_balancer_strategy: str = "round_robin"
    instances: List[str] = None


class RateLimiter:
    """Advanced rate limiter with multiple strategies"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    ) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed under rate limit"""
        
        if strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._sliding_window_check(key, limit, window)
        elif strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._fixed_window_check(key, limit, window)
        elif strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._token_bucket_check(key, limit, window)
        else:
            return await self._leaky_bucket_check(key, limit, window)
    
    async def _sliding_window_check(self, key: str, limit: int, window: int) -> tuple[bool, Dict]:
        """Sliding window rate limiting"""
        now = time.time()
        pipeline = self.redis.pipeline()
        
        # Remove old entries
        pipeline.zremrangebyscore(key, 0, now - window)
        
        # Count current requests
        pipeline.zcard(key)
        
        # Add current request
        pipeline.zadd(key, {str(uuid.uuid4()): now})
        
        # Set expiry
        pipeline.expire(key, window)
        
        results = await pipeline.execute()
        current_count = results[1]
        
        allowed = current_count < limit
        
        return allowed, {
            "limit": limit,
            "remaining": max(0, limit - current_count - 1) if allowed else 0,
            "reset_time": int(now + window),
            "retry_after": window if not allowed else None
        }
    
    async def _fixed_window_check(self, key: str, limit: int, window: int) -> tuple[bool, Dict]:
        """Fixed window rate limiting"""
        now = int(time.time())
        window_start = (now // window) * window
        window_key = f"{key}:{window_start}"
        
        current_count = await self.redis.incr(window_key)
        if current_count == 1:
            await self.redis.expire(window_key, window)
        
        allowed = current_count <= limit
        
        return allowed, {
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "reset_time": window_start + window,
            "retry_after": window_start + window - now if not allowed else None
        }
    
    async def _token_bucket_check(self, key: str, limit: int, window: int) -> tuple[bool, Dict]:
        """Token bucket rate limiting"""
        now = time.time()
        
        # Get current bucket state
        bucket_data = await self.redis.hmget(key, "tokens", "last_refill")
        
        tokens = float(bucket_data[0] or limit)
        last_refill = float(bucket_data[1] or now)
        
        # Calculate tokens to add
        time_passed = now - last_refill
        tokens_to_add = (time_passed / window) * limit
        tokens = min(limit, tokens + tokens_to_add)
        
        allowed = tokens >= 1
        
        if allowed:
            tokens -= 1
        
        # Update bucket state
        await self.redis.hmset(key, {
            "tokens": tokens,
            "last_refill": now
        })
        await self.redis.expire(key, window * 2)
        
        return allowed, {
            "limit": limit,
            "remaining": int(tokens),
            "reset_time": int(now + (limit - tokens) * (window / limit)) if tokens < limit else None,
            "retry_after": int((1 - tokens) * (window / limit)) if not allowed else None
        }
    
    async def _leaky_bucket_check(self, key: str, limit: int, window: int) -> tuple[bool, Dict]:
        """Leaky bucket rate limiting"""
        # Similar to token bucket but with constant leak rate
        # Implementation would be similar to token bucket
        return await self._token_bucket_check(key, limit, window)


class AuthenticationService:
    """Advanced authentication service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.jwt_secret = config.get("jwt_secret", "your-secret-key")
        self.jwt_algorithm = config.get("jwt_algorithm", "HS256")
        self.oauth2_config = config.get("oauth2", {})
    
    async def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return user info"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check expiration
            if payload.get("exp", 0) < time.time():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            return {
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "email": payload.get("email"),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", []),
                "scopes": payload.get("scopes", [])
            }
        
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    async def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """Verify API key and return associated service info"""
        # In production, this would query a database
        # For now, return mock data
        if api_key.startswith("ak_"):
            return {
                "service_id": "mock-service",
                "service_name": "Mock Service",
                "scopes": ["read", "write"],
                "rate_limit": 1000
            }
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    async def verify_oauth2_token(self, token: str) -> Dict[str, Any]:
        """Verify OAuth2 token"""
        # Implementation would validate with OAuth2 provider
        # For now, return mock data
        return {
            "user_id": "oauth2-user",
            "scopes": ["read", "write"],
            "client_id": "oauth2-client"
        }


class ServiceDiscovery:
    """Service discovery and load balancing"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.services: Dict[str, ServiceConfig] = {}
        self.health_checks = {}
    
    def register_service(self, service: ServiceConfig):
        """Register a microservice"""
        self.services[service.name] = service
        logger.info("Service registered", service=service.name, base_url=service.base_url)
    
    async def get_service_instance(self, service_name: str) -> Optional[str]:
        """Get available service instance using load balancing"""
        service = self.services.get(service_name)
        if not service:
            return None
        
        # For simplicity, return the base URL
        # In production, implement proper load balancing
        return service.base_url
    
    @circuit(failure_threshold=5, recovery_timeout=60, expected_exception=Exception)
    async def call_service(
        self,
        service_name: str,
        method: str,
        path: str,
        **kwargs
    ) -> httpx.Response:
        """Call microservice with circuit breaker"""
        instance_url = await self.get_service_instance(service_name)
        if not instance_url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service {service_name} not available"
            )
        
        service_config = self.services[service_name]
        url = f"{instance_url.rstrip('/')}/{path.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=service_config.timeout) as client:
            try:
                response = await client.request(method, url, **kwargs)
                return response
            except Exception as e:
                circuit_breaker_trips.labels(service=service_name).inc()
                logger.error("Service call failed", service=service_name, error=str(e))
                raise


class WebhookManager:
    """Webhook management and delivery"""
    
    def __init__(self, kafka_producer: KafkaProducer):
        self.kafka_producer = kafka_producer
        self.subscriptions: Dict[str, List[Dict]] = {}
    
    def subscribe(self, webhook_id: str, url: str, events: List[str], secret: str = None):
        """Subscribe to webhook events"""
        webhook = {
            "id": webhook_id,
            "url": url,
            "secret": secret,
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        }
        
        for event in events:
            if event not in self.subscriptions:
                self.subscriptions[event] = []
            self.subscriptions[event].append(webhook)
        
        logger.info("Webhook subscribed", webhook_id=webhook_id, events=events)
    
    async def trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger webhook event"""
        if event_type not in self.subscriptions:
            return
        
        event_payload = {
            "event_type": event_type,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Send to Kafka for async processing
        self.kafka_producer.send(
            "webhook-events",
            value=json.dumps(event_payload).encode('utf-8')
        )
        
        logger.info("Webhook event triggered", event_type=event_type, subscribers=len(self.subscriptions[event_type]))
    
    def generate_signature(self, payload: str, secret: str) -> str:
        """Generate webhook signature"""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()


class GraphQLService:
    """GraphQL service integration"""
    
    def __init__(self, service_discovery: ServiceDiscovery):
        self.service_discovery = service_discovery
        self.schema = self._build_schema()
    
    def _build_schema(self) -> graphene.Schema:
        """Build GraphQL schema"""
        
        class Customer(graphene.ObjectType):
            id = graphene.ID()
            first_name = graphene.String()
            last_name = graphene.String()
            email = graphene.String()
            phone = graphene.String()
            status = graphene.String()
        
        class Account(graphene.ObjectType):
            id = graphene.ID()
            account_number = graphene.String()
            customer_id = graphene.ID()
            account_type = graphene.String()
            balance = graphene.Float()
            currency = graphene.String()
            status = graphene.String()
        
        class Query(graphene.ObjectType):
            customer = graphene.Field(Customer, customer_id=graphene.ID(required=True))
            customers = graphene.List(Customer, limit=graphene.Int(), offset=graphene.Int())
            account = graphene.Field(Account, account_id=graphene.ID(required=True))
            accounts = graphene.List(Account, customer_id=graphene.ID())
            
            async def resolve_customer(self, info, customer_id):
                # Call customer service
                response = await self.service_discovery.call_service(
                    "customer-service",
                    "GET",
                    f"/customers/{customer_id}"
                )
                if response.status_code == 200:
                    data = response.json()
                    return Customer(**data)
                return None
            
            async def resolve_customers(self, info, limit=20, offset=0):
                # Call customer service
                response = await self.service_discovery.call_service(
                    "customer-service",
                    "GET",
                    f"/customers?limit={limit}&offset={offset}"
                )
                if response.status_code == 200:
                    data = response.json()
                    return [Customer(**customer) for customer in data.get("data", [])]
                return []
        
        class Mutation(graphene.ObjectType):
            create_customer = graphene.Field(Customer, input=graphene.Argument(graphene.String))
            
            async def resolve_create_customer(self, info, input):
                # Call customer service
                response = await self.service_discovery.call_service(
                    "customer-service",
                    "POST",
                    "/customers",
                    json=json.loads(input)
                )
                if response.status_code == 201:
                    data = response.json()
                    return Customer(**data)
                return None
        
        return graphene.Schema(query=Query, mutation=Mutation)
    
    async def execute_query(self, query: str, variables: Dict = None, context: Dict = None):
        """Execute GraphQL query"""
        result = await self.schema.execute_async(
            query,
            variables=variables,
            context=context,
            executor=AsyncioExecutor()
        )
        
        return {
            "data": result.data,
            "errors": [{"message": str(error)} for error in result.errors] if result.errors else None
        }


class APIGatewayMiddleware(BaseHTTPMiddleware):
    """Main API Gateway middleware"""
    
    def __init__(
        self,
        app,
        auth_service: AuthenticationService,
        rate_limiter: RateLimiter,
        service_discovery: ServiceDiscovery,
        webhook_manager: WebhookManager,
        config: Dict[str, Any]
    ):
        super().__init__(app)
        self.auth_service = auth_service
        self.rate_limiter = rate_limiter
        self.service_discovery = service_discovery
        self.webhook_manager = webhook_manager
        self.config = config
        self.endpoints: Dict[str, APIEndpointConfig] = {}
    
    def register_endpoint(self, endpoint_config: APIEndpointConfig):
        """Register API endpoint configuration"""
        self.endpoints[endpoint_config.path] = endpoint_config
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Process request through gateway middleware"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Add request ID to headers
        request.state.request_id = request_id
        
        # Increment active connections
        active_connections.inc()
        
        try:
            # Find matching endpoint configuration
            endpoint_config = self._find_endpoint_config(request.url.path, request.method)
            
            if endpoint_config and not endpoint_config.enabled:
                return JSONResponse(
                    status_code=503,
                    content={"error": "Endpoint disabled", "request_id": request_id}
                )
            
            # Authentication
            if endpoint_config and endpoint_config.auth_required:
                user_context = await self._authenticate_request(request, endpoint_config)
                request.state.user = user_context
            
            # Rate limiting
            if endpoint_config and endpoint_config.rate_limit:
                allowed, rate_info = await self._check_rate_limit(request, endpoint_config)
                if not allowed:
                    rate_limit_hits.labels(endpoint=endpoint_config.path).inc()
                    response = JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate limit exceeded",
                            "request_id": request_id,
                            **rate_info
                        }
                    )
                    response.headers.update({
                        "X-RateLimit-Limit": str(rate_info["limit"]),
                        "X-RateLimit-Remaining": str(rate_info["remaining"]),
                        "X-RateLimit-Reset": str(rate_info["reset_time"])
                    })
                    return response
            
            # Authorization
            if endpoint_config and (endpoint_config.roles_required or endpoint_config.permissions_required):
                await self._authorize_request(request, endpoint_config)
            
            # Request size validation
            if endpoint_config and endpoint_config.request_size_limit:
                await self._validate_request_size(request, endpoint_config)
            
            # Process request
            response = await call_next(request)
            
            # Response transformation
            if endpoint_config and endpoint_config.response_transform:
                response = await self._transform_response(response, endpoint_config)
            
            # Add security headers
            response = self._add_security_headers(response, request_id)
            
            # Record metrics
            duration = time.time() - start_time
            request_duration.observe(duration)
            request_count.labels(
                method=request.method,
                endpoint=endpoint_config.path if endpoint_config else request.url.path,
                status=response.status_code
            ).inc()
            
            # Trigger webhook events
            if endpoint_config and endpoint_config.webhook_events:
                await self._trigger_webhook_events(request, response, endpoint_config)
            
            return response
        
        except HTTPException as e:
            # Handle HTTP exceptions
            response = JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.detail,
                    "request_id": request_id
                }
            )
            return self._add_security_headers(response, request_id)
        
        except Exception as e:
            # Handle unexpected errors
            logger.error("Unexpected error in gateway", error=str(e), traceback=traceback.format_exc())
            response = JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id
                }
            )
            return self._add_security_headers(response, request_id)
        
        finally:
            # Decrement active connections
            active_connections.dec()
    
    def _find_endpoint_config(self, path: str, method: str) -> Optional[APIEndpointConfig]:
        """Find matching endpoint configuration"""
        # Simple path matching - in production, use more sophisticated routing
        for endpoint_path, config in self.endpoints.items():
            if endpoint_path in path and method in config.methods:
                return config
        return None
    
    async def _authenticate_request(self, request: Request, config: APIEndpointConfig) -> Dict[str, Any]:
        """Authenticate request based on configuration"""
        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("X-API-Key")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            return await self.auth_service.verify_jwt_token(token)
        
        elif api_key_header:
            return await self.auth_service.verify_api_key(api_key_header)
        
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
    
    async def _check_rate_limit(self, request: Request, config: APIEndpointConfig) -> tuple[bool, Dict]:
        """Check rate limit for request"""
        # Use user ID or IP address as key
        user_id = getattr(request.state, "user", {}).get("user_id")
        key = f"rate_limit:{config.path}:{user_id or request.client.host}"
        
        return await self.rate_limiter.is_allowed(
            key,
            config.rate_limit,
            config.rate_limit_window,
            config.rate_limit_strategy
        )
    
    async def _authorize_request(self, request: Request, config: APIEndpointConfig):
        """Authorize request based on roles and permissions"""
        user = getattr(request.state, "user", {})
        user_roles = set(user.get("roles", []))
        user_permissions = set(user.get("permissions", []))
        
        if config.roles_required:
            required_roles = set(config.roles_required)
            if not user_roles.intersection(required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient roles"
                )
        
        if config.permissions_required:
            required_permissions = set(config.permissions_required)
            if not user_permissions.intersection(required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
    
    async def _validate_request_size(self, request: Request, config: APIEndpointConfig):
        """Validate request size"""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > config.request_size_limit:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request too large"
            )
    
    async def _transform_response(self, response: StarletteResponse, config: APIEndpointConfig) -> StarletteResponse:
        """Transform response based on configuration"""
        # Implementation would apply response transformations
        return response
    
    def _add_security_headers(self, response: StarletteResponse, request_id: str) -> StarletteResponse:
        """Add security headers to response"""
        response.headers.update({
            "X-Request-ID": request_id,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        })
        return response
    
    async def _trigger_webhook_events(self, request: Request, response: StarletteResponse, config: APIEndpointConfig):
        """Trigger webhook events based on endpoint configuration"""
        for event_type in config.webhook_events:
            await self.webhook_manager.trigger_event(event_type, {
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "user_id": getattr(request.state, "user", {}).get("user_id"),
                "timestamp": datetime.utcnow().isoformat()
            })


class AdvancedAPIGateway:
    """Advanced API Gateway for CBS_PYTHON V2.0"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app = FastAPI(
            title="CBS_PYTHON V2.0 API Gateway",
            description="Advanced Core Banking System API Gateway",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Initialize components
        self.redis_client = None
        self.auth_service = AuthenticationService(config.get("auth", {}))
        self.rate_limiter = None
        self.service_discovery = None
        self.webhook_manager = None
        self.graphql_service = None
        
        # Setup app
        self._setup_middleware()
        self._setup_routes()
    
    async def startup(self):
        """Initialize async components"""
        # Initialize Redis
        redis_url = self.config.get("redis_url", "redis://localhost:6379")
        self.redis_client = aioredis.from_url(redis_url)
        
        # Initialize components
        self.rate_limiter = RateLimiter(self.redis_client)
        self.service_discovery = ServiceDiscovery(self.redis_client)
        
        # Initialize Kafka producer
        kafka_config = self.config.get("kafka", {})
        kafka_producer = KafkaProducer(
            bootstrap_servers=kafka_config.get("bootstrap_servers", ["localhost:9092"]),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.webhook_manager = WebhookManager(kafka_producer)
        
        # Initialize GraphQL
        self.graphql_service = GraphQLService(self.service_discovery)
        
        # Register services
        self._register_services()
        
        logger.info("API Gateway started successfully")
    
    async def shutdown(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()
        logger.info("API Gateway shutdown complete")
    
    def _setup_middleware(self):
        """Setup middleware stack"""
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.get("cors_origins", ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Trusted hosts
        if self.config.get("trusted_hosts"):
            self.app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=self.config["trusted_hosts"]
            )
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            services_status = {}
            for service_name in self.service_discovery.services.keys():
                try:
                    response = await self.service_discovery.call_service(
                        service_name, "GET", "/health"
                    )
                    services_status[service_name] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    }
                except Exception:
                    services_status[service_name] = {
                        "status": "unhealthy",
                        "response_time_ms": None
                    }
            
            overall_status = "healthy" if all(
                s["status"] == "healthy" for s in services_status.values()
            ) else "degraded"
            
            return {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "services": services_status,
                "version": "2.0.0"
            }
        
        @self.app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint"""
            return PlainTextResponse(generate_latest())
        
        @self.app.post("/v2/graphql")
        async def graphql_endpoint(request: Request):
            """GraphQL endpoint"""
            body = await request.json()
            query = body.get("query")
            variables = body.get("variables")
            operation_name = body.get("operationName")
            
            result = await self.graphql_service.execute_query(
                query, variables, {"request": request}
            )
            
            return result
        
        # Add proxy routes for each service
        self._setup_proxy_routes()
    
    def _setup_proxy_routes(self):
        """Setup proxy routes to microservices"""
        
        async def proxy_to_service(service_name: str, request: Request, path: str = ""):
            """Proxy request to microservice"""
            method = request.method
            url_path = path or request.url.path
            
            # Remove service prefix from path
            service_path = url_path.replace(f"/v2/{service_name}", "")
            
            # Get request body for POST/PUT requests
            body = None
            if method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
            
            # Prepare headers
            headers = dict(request.headers)
            # Remove host header to avoid conflicts
            headers.pop("host", None)
            
            try:
                response = await self.service_discovery.call_service(
                    service_name,
                    method,
                    service_path,
                    content=body,
                    headers=headers,
                    params=dict(request.query_params)
                )
                
                return JSONResponse(
                    status_code=response.status_code,
                    content=response.json() if response.content else None,
                    headers=dict(response.headers)
                )
            
            except Exception as e:
                logger.error("Service proxy error", service=service_name, error=str(e))
                return JSONResponse(
                    status_code=503,
                    content={"error": f"Service {service_name} unavailable"}
                )
        
        # Add routes for each service
        services = ["customers", "accounts", "transactions", "payments", "loans", "notifications", "audit"]
        for service in services:
            self.app.api_route(
                f"/v2/{service}/{{path:path}}",
                methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
                endpoint=lambda req, p, s=service: proxy_to_service(f"{s}-service", req, p)
            )
    
    def _register_services(self):
        """Register microservices"""
        services = [
            ServiceConfig(
                name="customer-service",
                base_url=self.config.get("services", {}).get("customer", "http://customer-service:8000")
            ),
            ServiceConfig(
                name="account-service",
                base_url=self.config.get("services", {}).get("account", "http://account-service:8000")
            ),
            ServiceConfig(
                name="transaction-service",
                base_url=self.config.get("services", {}).get("transaction", "http://transaction-service:8000")
            ),
            ServiceConfig(
                name="payment-service",
                base_url=self.config.get("services", {}).get("payment", "http://payment-service:8000")
            ),
            ServiceConfig(
                name="loan-service",
                base_url=self.config.get("services", {}).get("loan", "http://loan-service:8000")
            ),
            ServiceConfig(
                name="notification-service",
                base_url=self.config.get("services", {}).get("notification", "http://notification-service:8000")
            ),
            ServiceConfig(
                name="audit-service",
                base_url=self.config.get("services", {}).get("audit", "http://audit-service:8000")
            )
        ]
        
        for service in services:
            self.service_discovery.register_service(service)
    
    def add_middleware_after_startup(self):
        """Add gateway middleware after startup"""
        gateway_middleware = APIGatewayMiddleware(
            self.app,
            self.auth_service,
            self.rate_limiter,
            self.service_discovery,
            self.webhook_manager,
            self.config
        )
        
        # Register endpoint configurations
        self._register_endpoint_configs(gateway_middleware)
        
        self.app.add_middleware(APIGatewayMiddleware, **{
            "auth_service": self.auth_service,
            "rate_limiter": self.rate_limiter,
            "service_discovery": self.service_discovery,
            "webhook_manager": self.webhook_manager,
            "config": self.config
        })
    
    def _register_endpoint_configs(self, middleware: APIGatewayMiddleware):
        """Register endpoint configurations"""
        configs = [
            APIEndpointConfig(
                path="/v2/customers",
                methods=["GET", "POST"],
                rate_limit=100,
                roles_required=["customer_manager", "admin"],
                webhook_events=["customer.created", "customer.updated"]
            ),
            APIEndpointConfig(
                path="/v2/accounts",
                methods=["GET", "POST"],
                rate_limit=200,
                roles_required=["account_manager", "admin"],
                webhook_events=["account.created", "account.status_changed"]
            ),
            APIEndpointConfig(
                path="/v2/transactions",
                methods=["GET", "POST"],
                rate_limit=500,
                roles_required=["transaction_processor", "admin"],
                webhook_events=["transaction.created", "transaction.completed"]
            ),
            APIEndpointConfig(
                path="/v2/payments",
                methods=["GET", "POST"],
                rate_limit=300,
                roles_required=["payment_processor", "admin"],
                webhook_events=["payment.created", "payment.completed", "payment.failed"]
            ),
            APIEndpointConfig(
                path="/v2/loans",
                methods=["GET", "POST"],
                rate_limit=50,
                roles_required=["loan_officer", "admin"],
                webhook_events=["loan.application_submitted", "loan.approved", "loan.disbursed"]
            )
        ]
        
        for config in configs:
            middleware.register_endpoint(config)


# Factory function
def create_gateway(config: Dict[str, Any]) -> AdvancedAPIGateway:
    """Create and configure API Gateway"""
    return AdvancedAPIGateway(config)


if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    config = {
        "auth": {
            "jwt_secret": "your-super-secret-key",
            "jwt_algorithm": "HS256"
        },
        "redis_url": "redis://localhost:6379",
        "kafka": {
            "bootstrap_servers": ["localhost:9092"]
        },
        "services": {
            "customer": "http://localhost:8001",
            "account": "http://localhost:8002",
            "transaction": "http://localhost:8003",
            "payment": "http://localhost:8004",
            "loan": "http://localhost:8005",
            "notification": "http://localhost:8006",
            "audit": "http://localhost:8007"
        },
        "cors_origins": ["*"],
        "trusted_hosts": ["localhost", "127.0.0.1"]
    }
    
    # Create gateway
    gateway = create_gateway(config)
    
    # Add startup and shutdown events
    @gateway.app.on_event("startup")
    async def startup():
        await gateway.startup()
        gateway.add_middleware_after_startup()
    
    @gateway.app.on_event("shutdown")
    async def shutdown():
        await gateway.shutdown()
    
    # Run the server
    uvicorn.run(
        gateway.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
