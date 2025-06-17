"""
Gateway Service Configuration
Configuration management for the API Gateway
"""

from pydantic import BaseSettings, Field
from typing import List, Dict, Any, Optional
import os


class SecurityConfig(BaseSettings):
    """Security configuration"""
    secret_key: str = Field(default="your-super-secret-key-change-in-production", env="JWT_SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    allowed_hosts: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    default_rate_limit: str = Field(default="100/minute", env="DEFAULT_RATE_LIMIT")
    
    # API Key settings
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    master_api_key: Optional[str] = Field(default=None, env="MASTER_API_KEY")


class CorsConfig(BaseSettings):
    """CORS configuration"""
    allow_origins: List[str] = Field(default=["*"], env="CORS_ALLOW_ORIGINS")
    allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")


class ServiceConfig(BaseSettings):
    """Individual service configuration"""
    name: str
    host: str
    port: int
    protocol: str = "http"
    health_check_path: str = "/health"
    timeout: int = 30
    retries: int = 3
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60
    
    @property
    def base_url(self) -> str:
        """Get the base URL for the service"""
        return f"{self.protocol}://{self.host}:{self.port}"


class ServicesConfig(BaseSettings):
    """Services configuration"""
    customer_service: ServiceConfig = Field(
        default=ServiceConfig(
            name="customer-service",
            host=os.getenv("CUSTOMER_SERVICE_HOST", "localhost"),
            port=int(os.getenv("CUSTOMER_SERVICE_PORT", "8001"))
        )
    )
    
    account_service: ServiceConfig = Field(
        default=ServiceConfig(
            name="account-service",
            host=os.getenv("ACCOUNT_SERVICE_HOST", "localhost"),
            port=int(os.getenv("ACCOUNT_SERVICE_PORT", "8002"))
        )
    )
    
    payment_service: ServiceConfig = Field(
        default=ServiceConfig(
            name="payment-service",
            host=os.getenv("PAYMENT_SERVICE_HOST", "localhost"),
            port=int(os.getenv("PAYMENT_SERVICE_PORT", "8003"))
        )
    )
    
    transaction_service: ServiceConfig = Field(
        default=ServiceConfig(
            name="transaction-service",
            host=os.getenv("TRANSACTION_SERVICE_HOST", "localhost"),
            port=int(os.getenv("TRANSACTION_SERVICE_PORT", "8004"))
        )
    )
    
    loan_service: ServiceConfig = Field(
        default=ServiceConfig(
            name="loan-service",
            host=os.getenv("LOAN_SERVICE_HOST", "localhost"),
            port=int(os.getenv("LOAN_SERVICE_PORT", "8005"))
        )
    )
    
    notification_service: ServiceConfig = Field(
        default=ServiceConfig(
            name="notification-service",
            host=os.getenv("NOTIFICATION_SERVICE_HOST", "localhost"),
            port=int(os.getenv("NOTIFICATION_SERVICE_PORT", "8006"))
        )
    )
    
    audit_service: ServiceConfig = Field(
        default=ServiceConfig(
            name="audit-service",
            host=os.getenv("AUDIT_SERVICE_HOST", "localhost"),
            port=int(os.getenv("AUDIT_SERVICE_PORT", "8007"))
        )
    )
    
    def get_service(self, name: str) -> Optional[ServiceConfig]:
        """Get service configuration by name"""
        return getattr(self, f"{name.replace('-', '_')}", None)
    
    def get_all_services(self) -> Dict[str, ServiceConfig]:
        """Get all service configurations"""
        return {
            "customer-service": self.customer_service,
            "account-service": self.account_service,
            "payment-service": self.payment_service,
            "transaction-service": self.transaction_service,
            "loan-service": self.loan_service,
            "notification-service": self.notification_service,
            "audit-service": self.audit_service
        }


class RateLimitConfig(BaseSettings):
    """Rate limiting configuration"""
    enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    default_limit: str = Field(default="100/minute", env="DEFAULT_RATE_LIMIT")
    
    # Endpoint-specific rate limits
    auth_limit: str = Field(default="10/minute", env="AUTH_RATE_LIMIT")
    transaction_limit: str = Field(default="50/minute", env="TRANSACTION_RATE_LIMIT")
    payment_limit: str = Field(default="30/minute", env="PAYMENT_RATE_LIMIT")
    account_limit: str = Field(default="100/minute", env="ACCOUNT_RATE_LIMIT")
    
    # Burst settings
    burst_size: int = Field(default=10, env="RATE_LIMIT_BURST_SIZE")
    
    # Rate limit by user role
    admin_limit: str = Field(default="1000/minute", env="ADMIN_RATE_LIMIT")
    customer_limit: str = Field(default="100/minute", env="CUSTOMER_RATE_LIMIT")
    system_limit: str = Field(default="10000/minute", env="SYSTEM_RATE_LIMIT")


class MonitoringConfig(BaseSettings):
    """Monitoring and observability configuration"""
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    tracing_enabled: bool = Field(default=True, env="TRACING_ENABLED")
    logging_level: str = Field(default="INFO", env="LOGGING_LEVEL")
    
    # Prometheus metrics
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # Jaeger tracing
    jaeger_enabled: bool = Field(default=True, env="JAEGER_ENABLED")
    jaeger_agent_host: str = Field(default="localhost", env="JAEGER_AGENT_HOST")
    jaeger_agent_port: int = Field(default=6831, env="JAEGER_AGENT_PORT")
    
    # Health check intervals
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    health_check_timeout: int = Field(default=10, env="HEALTH_CHECK_TIMEOUT")


class CacheConfig(BaseSettings):
    """Caching configuration"""
    enabled: bool = Field(default=True, env="CACHE_ENABLED")
    redis_url: str = Field(default="redis://localhost:6379/1", env="CACHE_REDIS_URL")
    default_ttl: int = Field(default=300, env="CACHE_DEFAULT_TTL")  # 5 minutes
    
    # Cache settings by endpoint type
    auth_cache_ttl: int = Field(default=900, env="AUTH_CACHE_TTL")  # 15 minutes
    user_info_cache_ttl: int = Field(default=600, env="USER_INFO_CACHE_TTL")  # 10 minutes
    account_cache_ttl: int = Field(default=300, env="ACCOUNT_CACHE_TTL")  # 5 minutes
    
    # Cache invalidation
    invalidation_enabled: bool = Field(default=True, env="CACHE_INVALIDATION_ENABLED")


class LoadBalancingConfig(BaseSettings):
    """Load balancing configuration"""
    algorithm: str = Field(default="round_robin", env="LOAD_BALANCE_ALGORITHM")  # round_robin, least_connections, weighted
    health_check_enabled: bool = Field(default=True, env="HEALTH_CHECK_ENABLED")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # Circuit breaker settings
    circuit_breaker_enabled: bool = Field(default=True, env="CIRCUIT_BREAKER_ENABLED")
    failure_threshold: int = Field(default=5, env="CIRCUIT_BREAKER_FAILURE_THRESHOLD")
    recovery_timeout: int = Field(default=60, env="CIRCUIT_BREAKER_RECOVERY_TIMEOUT")
    
    # Retry settings
    retry_enabled: bool = Field(default=True, env="RETRY_ENABLED")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay: float = Field(default=1.0, env="RETRY_DELAY")
    backoff_factor: float = Field(default=2.0, env="RETRY_BACKOFF_FACTOR")


class GatewayConfig(BaseSettings):
    """Main gateway configuration"""
    # Basic settings
    host: str = Field(default="0.0.0.0", env="GATEWAY_HOST")
    port: int = Field(default=8000, env="GATEWAY_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Component configurations
    security: SecurityConfig = SecurityConfig()
    cors: CorsConfig = CorsConfig()
    services: ServicesConfig = ServicesConfig()
    rate_limiting: RateLimitConfig = RateLimitConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    cache: CacheConfig = CacheConfig()
    load_balancing: LoadBalancingConfig = LoadBalancingConfig()
    
    # API versioning
    api_version: str = Field(default="v1", env="API_VERSION")
    api_prefix: str = Field(default="/api", env="API_PREFIX")
    
    # Request/Response settings
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # Error handling
    include_error_details: bool = Field(default=False, env="INCLUDE_ERROR_DETAILS")
    log_requests: bool = Field(default=True, env="LOG_REQUESTS")
    log_responses: bool = Field(default=False, env="LOG_RESPONSES")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Route configuration
ROUTE_MAPPINGS = {
    # Customer Service Routes
    "/api/v1/customers": "customer-service",
    "/api/v1/customers/{path:path}": "customer-service",
    
    # Account Service Routes
    "/api/v1/accounts": "account-service",
    "/api/v1/accounts/{path:path}": "account-service",
    
    # Payment Service Routes
    "/api/v1/payments": "payment-service",
    "/api/v1/payments/{path:path}": "payment-service",
    "/api/v1/transfers": "payment-service",
    "/api/v1/transfers/{path:path}": "payment-service",
    
    # Transaction Service Routes
    "/api/v1/transactions": "transaction-service",
    "/api/v1/transactions/{path:path}": "transaction-service",
    
    # Loan Service Routes
    "/api/v1/loans": "loan-service",
    "/api/v1/loans/{path:path}": "loan-service",
    
    # Notification Service Routes
    "/api/v1/notifications": "notification-service",
    "/api/v1/notifications/{path:path}": "notification-service",
    
    # Audit Service Routes
    "/api/v1/audit": "audit-service",
    "/api/v1/audit/{path:path}": "audit-service",
}

# Rate limit overrides for specific endpoints
ENDPOINT_RATE_LIMITS = {
    "POST /api/v1/auth/login": "10/minute",
    "POST /api/v1/auth/register": "5/minute",
    "POST /api/v1/payments": "30/minute",
    "POST /api/v1/transfers": "20/minute",
    "POST /api/v1/loans/applications": "5/minute",
    "GET /api/v1/accounts/{account_id}/balance": "50/minute",
    "GET /api/v1/transactions": "100/minute",
}

# Authentication bypass routes (public endpoints)
PUBLIC_ROUTES = [
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/metrics",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/forgot-password",
]

# Admin-only routes
ADMIN_ROUTES = [
    "/api/v1/admin",
    "/api/v1/audit",
    "/api/v1/system",
]

# System routes (internal service communication)
SYSTEM_ROUTES = [
    "/api/v1/internal",
]


def get_config() -> GatewayConfig:
    """Get gateway configuration instance"""
    return GatewayConfig()


__all__ = [
    "GatewayConfig",
    "SecurityConfig",
    "CorsConfig",
    "ServiceConfig",
    "ServicesConfig",
    "RateLimitConfig",
    "MonitoringConfig",
    "CacheConfig",
    "LoadBalancingConfig",
    "ROUTE_MAPPINGS",
    "ENDPOINT_RATE_LIMITS",
    "PUBLIC_ROUTES",
    "ADMIN_ROUTES",
    "SYSTEM_ROUTES",
    "get_config"
]
