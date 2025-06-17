"""
CBS Platform API Gateway V2.0 - Main Application
Advanced Central API Gateway with comprehensive security, monitoring, and performance features
"""

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import httpx
import time
import logging
import uuid
from typing import Dict, Any, Optional
import asyncio
from contextlib import asynccontextmanager

from platform.shared.auth import AuthenticationService, TokenData, AuthConfig
from platform.shared.events import EventBus, LoggingEventHandler
from .config import GatewayConfig, ROUTE_MAPPINGS, PUBLIC_ROUTES, ADMIN_ROUTES, ENDPOINT_RATE_LIMITS
from .middleware import (
    RateLimitMiddleware, LoggingMiddleware, MetricsMiddleware,
    AuthenticationMiddleware, CacheMiddleware, CircuitBreakerMiddleware,
    AuditMiddleware, CompressionMiddleware, SecurityHeadersMiddleware
)
from .routing import ServiceRouter
from .health import HealthChecker

logger = logging.getLogger(__name__)


class APIGateway:
    """Enhanced API Gateway service for routing and managing requests"""
    
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.auth_service = AuthenticationService(
            AuthConfig(
                secret_key=config.security.secret_key,
                algorithm=config.security.algorithm,
                access_token_expire_minutes=config.security.access_token_expire_minutes
            )
        )
        self.security = HTTPBearer()
        self.service_router = ServiceRouter(config.services.get_all_services())
        self.health_checker = HealthChecker(config.services.get_all_services())
        self.event_bus = EventBus()
        
        # Setup event handlers
        self.event_bus.subscribe_all(LoggingEventHandler())
        
        # Initialize metrics
        self.start_time = time.time()
        self.requests_processed = 0
        
        self.app = self._create_app()
    
    def _create_app(self) -> FastAPI:
        """Create FastAPI application with middleware and routes"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            logger.info("Starting CBS Platform API Gateway V2.0...")
            await self.health_checker.start_health_checks()
            # Start background tasks
            await self.service_router.start_background_tasks()
            yield
            # Shutdown
            logger.info("Shutting down CBS Platform API Gateway V2.0...")
            await self.health_checker.stop_health_checks()
            await self.service_router.stop_background_tasks()
        
        app = FastAPI(
            title="CBS Platform API Gateway V2.0",
            description="Advanced Central API Gateway for Core Banking System with comprehensive security, monitoring, and performance features",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            lifespan=lifespan,
            contact={
                "name": "CBS Platform Team",
                "email": "platform@cbs.com"
            },
            license_info={
                "name": "MIT License",
                "url": "https://opensource.org/licenses/MIT"
            }
        )
        
        # Security Headers Middleware (applied first)
        app.add_middleware(SecurityHeadersMiddleware)
        
        # CORS Middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors.allow_origins,
            allow_credentials=self.config.cors.allow_credentials,
            allow_methods=self.config.cors.allow_methods,
            allow_headers=self.config.cors.allow_headers,
        )
        
        # Trusted Host Middleware
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=self.config.security.allowed_hosts
        )
        
        # Compression Middleware
        app.add_middleware(CompressionMiddleware)
        
        # Rate Limiting Middleware
        app.add_middleware(RateLimitMiddleware, 
                          config=self.config.rate_limiting,
                          endpoint_limits=ENDPOINT_RATE_LIMITS)
        
        # Authentication Middleware
        app.add_middleware(AuthenticationMiddleware,
                          auth_service=self.auth_service,
                          public_routes=PUBLIC_ROUTES,
                          admin_routes=ADMIN_ROUTES)
        
        # Cache Middleware
        app.add_middleware(CacheMiddleware, config=self.config.cache)
        
        # Audit Middleware (for compliance tracking)
        app.add_middleware(AuditMiddleware, event_bus=self.event_bus)
        
        # Circuit Breaker Middleware
        app.add_middleware(CircuitBreakerMiddleware, 
                          config=self.config.load_balancing,
                          service_router=self.service_router)
        
        # Metrics Middleware
        app.add_middleware(MetricsMiddleware, config=self.config.monitoring)
        
        # Logging Middleware (applied last to capture all requests)
        app.add_middleware(LoggingMiddleware, 
                          config=self.config.monitoring,
                          event_bus=self.event_bus)
        
        # Add routes
        self._setup_routes(app)
        
        return app

    def _setup_routes(self, app: FastAPI):
        """Setup comprehensive API routes for all V2.0 services"""
        
        # Health Check Endpoints
        @app.get("/health", tags=["Health"])
        async def health_check():
            """Basic health check endpoint"""
            return {
                "status": "healthy", 
                "timestamp": time.time(),
                "version": "2.0.0",
                "service": "api-gateway"
            }
        
        @app.get("/health/detailed", tags=["Health"])
        async def detailed_health_check():
            """Detailed health check with all service status"""
            service_health = await self.health_checker.check_all_services()
            overall_status = "healthy" if all(s["healthy"] for s in service_health.values()) else "unhealthy"
            
            return {
                "status": overall_status,
                "timestamp": time.time(),
                "version": "2.0.0",
                "gateway": {
                    "status": "healthy",
                    "uptime": time.time() - self.start_time,
                    "requests_processed": getattr(self, 'requests_processed', 0)
                },
                "services": service_health
            }

        @app.get("/health/live", tags=["Health"])
        async def liveness_check():
            """Kubernetes liveness probe"""
            return {"status": "alive"}

        @app.get("/health/ready", tags=["Health"])
        async def readiness_check():
            """Kubernetes readiness probe"""
            # Check if critical services are available
            critical_services = ["customer-service", "account-service", "transaction-service"]
            service_health = await self.health_checker.check_services(critical_services)
            
            if all(s["healthy"] for s in service_health.values()):
                return {"status": "ready"}
            else:
                raise HTTPException(status_code=503, detail="Service not ready")

        # Metrics and Monitoring
        @app.get("/metrics", tags=["Monitoring"])
        async def get_metrics():
            """Prometheus metrics endpoint"""
            # This would typically return Prometheus format metrics
            return {"message": "Metrics endpoint - integrate with Prometheus"}

        # Authentication Endpoints
        @app.post("/api/v1/auth/login", tags=["Authentication"])
        async def login(credentials: Dict[str, str]):
            """User authentication endpoint"""
            username = credentials.get("username")
            password = credentials.get("password")
            
            if not username or not password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username and password required"
                )
            
            # Enhanced authentication with user service integration
            try:
                # Route to customer service for authentication
                auth_result = await self._authenticate_user(username, password)
                
                if auth_result.get("success"):
                    user_data = auth_result["user"]
                    token_data = {
                        "user_id": user_data["user_id"],
                        "username": username,
                        "email": user_data.get("email"),
                        "roles": user_data.get("roles", ["customer"]),
                        "permissions": user_data.get("permissions", []),
                        "customer_id": user_data.get("customer_id")
                    }
                    
                    access_token = self.auth_service.create_access_token(token_data)
                    refresh_token = self.auth_service.create_refresh_token(token_data["user_id"])
                    
                    return {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "token_type": "bearer",
                        "expires_in": self.config.security.access_token_expire_minutes * 60,
                        "user": {
                            "user_id": user_data["user_id"],
                            "username": username,
                            "email": user_data.get("email"),
                            "roles": user_data.get("roles"),
                            "customer_id": user_data.get("customer_id")
                        }
                    }
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials"
                    )
            except Exception as e:
                logger.error(f"Authentication failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed"
                )

        @app.post("/api/v1/auth/refresh", tags=["Authentication"])
        async def refresh_token(refresh_request: Dict[str, str]):
            """Refresh access token"""
            refresh_token = refresh_request.get("refresh_token")
            if not refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Refresh token required"
                )
            
            try:
                token_data = self.auth_service.verify_token(refresh_token)
                new_token_data = {
                    "user_id": token_data.user_id,
                    "username": token_data.username,
                    "email": token_data.email,
                    "roles": token_data.roles,
                    "permissions": token_data.permissions,
                    "customer_id": getattr(token_data, 'customer_id', None)
                }
                access_token = self.auth_service.create_access_token(new_token_data)
                
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": self.config.security.access_token_expire_minutes * 60
                }
            except HTTPException:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )

        @app.post("/api/v1/auth/logout", tags=["Authentication"])
        async def logout(
            token_data: TokenData = Depends(self.get_current_user)
        ):
            """User logout endpoint"""
            # In a production system, you would invalidate the token
            # For now, just return success
            return {"message": "Successfully logged out"}

        # Customer Service Routes
        @app.api_route(
            "/api/v1/customers",
            methods=["GET", "POST"],
            tags=["Customer Management"]
        )
        @app.api_route(
            "/api/v1/customers/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            tags=["Customer Management"]
        )
        async def route_customer_service(
            request: Request,
            path: str = "",
            token_data: TokenData = Depends(self.get_current_user)
        ):
            """Route requests to customer service"""
            return await self._route_to_service("customer-service", request, path, token_data)

        # Account Service Routes
        @app.api_route(
            "/api/v1/accounts",
            methods=["GET", "POST"],
            tags=["Account Management"]
        )
        @app.api_route(
            "/api/v1/accounts/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            tags=["Account Management"]
        )
        async def route_account_service(
            request: Request,
            path: str = "",
            token_data: TokenData = Depends(self.get_current_user)
        ):
            """Route requests to account service"""
            return await self._route_to_service("account-service", request, path, token_data)

        # Transaction Service Routes
        @app.api_route(
            "/api/v1/transactions",
            methods=["GET", "POST"],
            tags=["Transaction Management"]
        )
        @app.api_route(
            "/api/v1/transactions/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            tags=["Transaction Management"]
        )
        async def route_transaction_service(
            request: Request,
            path: str = "",
            token_data: TokenData = Depends(self.get_current_user)
        ):
            """Route requests to transaction service"""
            return await self._route_to_service("transaction-service", request, path, token_data)

        # Payment Service Routes
        @app.api_route(
            "/api/v1/payments",
            methods=["GET", "POST"],
            tags=["Payment Processing"]
        )
        @app.api_route(
            "/api/v1/payments/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            tags=["Payment Processing"]
        )
        @app.api_route(
            "/api/v1/transfers",
            methods=["GET", "POST"],
            tags=["Payment Processing"]
        )
        @app.api_route(
            "/api/v1/transfers/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            tags=["Payment Processing"]
        )
        async def route_payment_service(
            request: Request,
            path: str = "",
            token_data: TokenData = Depends(self.get_current_user)
        ):
            """Route requests to payment service"""
            return await self._route_to_service("payment-service", request, path, token_data)

        # Loan Service Routes
        @app.api_route(
            "/api/v1/loans",
            methods=["GET", "POST"],
            tags=["Loan Management"]
        )
        @app.api_route(
            "/api/v1/loans/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            tags=["Loan Management"]
        )
        async def route_loan_service(
            request: Request,
            path: str = "",
            token_data: TokenData = Depends(self.get_current_user)
        ):
            """Route requests to loan service"""
            return await self._route_to_service("loan-service", request, path, token_data)

        # Notification Service Routes
        @app.api_route(
            "/api/v1/notifications",
            methods=["GET", "POST"],
            tags=["Notification Management"]
        )
        @app.api_route(
            "/api/v1/notifications/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            tags=["Notification Management"]
        )
        async def route_notification_service(
            request: Request,
            path: str = "",
            token_data: TokenData = Depends(self.get_current_user)
        ):
            """Route requests to notification service"""
            return await self._route_to_service("notification-service", request, path, token_data)

        # Audit Service Routes (Admin only)
        @app.api_route(
            "/api/v1/audit",
            methods=["GET", "POST"],
            tags=["Audit & Compliance"]
        )
        @app.api_route(
            "/api/v1/audit/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            tags=["Audit & Compliance"]
        )
        async def route_audit_service(
            request: Request,
            path: str = "",
            token_data: TokenData = Depends(self.get_current_user)
        ):
            """Route requests to audit service (Admin access required)"""
            # Check admin permissions
            if not self._has_admin_access(token_data):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required for audit operations"
                )
            return await self._route_to_service("audit-service", request, path, token_data)

        # Service Discovery Endpoint
        @app.get("/api/v1/services", tags=["Service Discovery"])
        async def get_services(
            token_data: TokenData = Depends(self.get_current_user)
        ):
            """Get available services and their status"""
            services = await self.health_checker.check_all_services()
            return {
                "services": services,
                "gateway_version": "2.0.0",
                "total_services": len(services),
                "healthy_services": sum(1 for s in services.values() if s["healthy"])
            }

        # Admin Endpoints
        @app.get("/api/v1/admin/config", tags=["Administration"])
        async def get_gateway_config(
            token_data: TokenData = Depends(self.get_current_user)
        ):
            """Get gateway configuration (Admin only)"""
            if not self._has_admin_access(token_data):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
            
            return {
                "version": "2.0.0",
                "environment": self.config.environment,
                "services": list(self.config.services.get_all_services().keys()),
                "features": {
                    "rate_limiting": self.config.rate_limiting.enabled,
                    "caching": self.config.cache.enabled,
                    "circuit_breaker": self.config.load_balancing.circuit_breaker_enabled,
                    "monitoring": self.config.monitoring.metrics_enabled,
                    "tracing": self.config.monitoring.tracing_enabled
                }
            }

    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Extract current user from JWT token"""
        try:
            token_data = self.auth_service.verify_token(credentials.credentials)
            return token_data
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )

    def _has_admin_access(self, token_data: TokenData) -> bool:
        """Check if user has admin access"""
        if not token_data or not token_data.roles:
            return False
        return "admin" in token_data.roles or "system" in token_data.roles

    async def _authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user against customer service"""
        try:
            # In production, this would route to customer service authentication endpoint
            customer_service_url = await self.service_router.get_service_url("customer-service")
            if not customer_service_url:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Customer service unavailable"
                )

            async with httpx.AsyncClient(timeout=30.0) as client:
                auth_data = {
                    "username": username,
                    "password": password
                }
                
                response = await client.post(
                    f"{customer_service_url}/auth/login",
                    json=auth_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"success": False, "message": "Authentication failed"}

        except httpx.RequestError as e:
            logger.error(f"Customer service authentication request failed: {str(e)}")
            # Fallback for demo purposes
            if username == "admin" and password == "admin":
                return {
                    "success": True,
                    "user": {
                        "user_id": "admin-123",
                        "username": username,
                        "email": "admin@cbs.com",
                        "roles": ["admin"],
                        "permissions": ["admin:read", "admin:write", "admin:system"],
                        "customer_id": "admin-customer-123"
                    }
                }
            elif username == "user" and password == "user":
                return {
                    "success": True,
                    "user": {
                        "user_id": "user-123",
                        "username": username,
                        "email": "user@cbs.com",
                        "roles": ["customer"],
                        "permissions": ["customer:read", "customer:write"],
                        "customer_id": "customer-123"
                    }
                }
            return {"success": False, "message": "Authentication failed"}

    async def _route_to_service(
        self, 
        service_name: str, 
        request: Request, 
        path: str, 
        token_data: TokenData
    ) -> JSONResponse:
        """Route request to target service with enhanced error handling and monitoring"""
        try:
            # Get service URL with load balancing
            service_url = await self.service_router.get_service_url(service_name)
            if not service_url:
                await self.event_bus.publish("service_unavailable", {
                    "service": service_name,
                    "timestamp": time.time(),
                    "user_id": token_data.user_id if token_data else None
                })
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Service {service_name} is unavailable"
                )

            # Build target URL
            target_url = f"{service_url}/{path}" if path else service_url
            if request.url.query:
                target_url += f"?{request.url.query}"

            # Prepare headers
            headers = dict(request.headers)
            headers["X-User-ID"] = token_data.user_id
            headers["X-User-Roles"] = ",".join(token_data.roles) if token_data.roles else ""
            headers["X-Customer-ID"] = getattr(token_data, 'customer_id', '') or ''
            headers["X-Request-ID"] = str(uuid.uuid4())
            headers["X-Gateway-Version"] = "2.0.0"
            
            # Remove host header to avoid conflicts
            headers.pop("host", None)

            # Get request body
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                except Exception as e:
                    logger.warning(f"Failed to read request body: {str(e)}")

            # Make request with circuit breaker and retry logic
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                    follow_redirects=True
                )

            response_time = time.time() - start_time

            # Update service router with response metrics
            await self.service_router.update_service_metrics(
                service_name, response_time, response.status_code < 500
            )

            # Publish successful routing event
            await self.event_bus.publish("request_routed", {
                "service": service_name,
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "response_time": response_time,
                "user_id": token_data.user_id if token_data else None,
                "timestamp": time.time()
            })

            # Return response
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"data": response.text},
                status_code=response.status_code,
                headers={
                    "X-Service": service_name,
                    "X-Response-Time": str(response_time),
                    "X-Gateway-Version": "2.0.0"
                }
            )

        except httpx.TimeoutException:
            logger.error(f"Timeout routing to {service_name}: {path}")
            await self.event_bus.publish("request_timeout", {
                "service": service_name,
                "path": path,
                "user_id": token_data.user_id if token_data else None,
                "timestamp": time.time()
            })
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Request to {service_name} timed out"
            )
        
        except httpx.RequestError as e:
            logger.error(f"Error routing to {service_name}: {str(e)}")
            await self.event_bus.publish("request_error", {
                "service": service_name,
                "error": str(e),
                "path": path,
                "user_id": token_data.user_id if token_data else None,
                "timestamp": time.time()
            })
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error communicating with {service_name}"
            )
        
        except Exception as e:
            logger.error(f"Unexpected error routing to {service_name}: {str(e)}")
            await self.event_bus.publish("gateway_error", {
                "service": service_name,
                "error": str(e),
                "path": path,
                "user_id": token_data.user_id if token_data else None,
                "timestamp": time.time()
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal gateway error"
            )

    async def start(self):
        """Start the gateway service"""
        logger.info("Starting CBS Platform API Gateway V2.0...")
        self.start_time = time.time()
        self.requests_processed = 0

    async def stop(self):
        """Stop the gateway service"""
        logger.info("Stopping CBS Platform API Gateway V2.0...")
        await self.health_checker.stop_health_checks()
        await self.service_router.stop_background_tasks()


def create_app(config: Optional[GatewayConfig] = None) -> FastAPI:
    """Factory function to create FastAPI application"""
    if config is None:
        config = GatewayConfig()
    
    gateway = APIGateway(config)
    return gateway.app


# Application entry point
if __name__ == "__main__":
    try:
        import uvicorn
        
        # Load configuration
        config = GatewayConfig()
        
        # Create application
        app = create_app(config)
        
        # Run server
        uvicorn.run(
            app,
            host=config.host,
            port=config.port,
            log_level=config.monitoring.logging_level.lower(),
            access_log=config.log_requests,
            reload=config.debug
        )
    except ImportError:
        logger.error("uvicorn not available. Use: pip install uvicorn")
        logger.info("You can also run with: python -m uvicorn main:app --host 0.0.0.0 --port 8000")
