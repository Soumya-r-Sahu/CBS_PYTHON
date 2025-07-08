"""
Configuration Management for CBS Platform V2.0 API Gateway
Comprehensive configuration with encryption, security, and deployment settings.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import yaml

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class EncryptionConfig:
    """Encryption configuration settings."""
    enabled: bool = True
    enforce_encryption: bool = False
    master_key: str = field(default_factory=lambda: os.getenv("CBS_MASTER_ENCRYPTION_KEY", "dev-key-change-in-production"))
    key_rotation_hours: int = 24
    algorithm: str = "AES-256-GCM"
    key_derivation: str = "HKDF"
    encrypted_routes: List[str] = field(default_factory=lambda: [
        "/api/v1/payments",
        "/api/v1/transactions",
        "/api/v1/accounts",
        "/api/v1/auth"
    ])
    bypass_routes: List[str] = field(default_factory=lambda: [
        "/health",
        "/docs", 
        "/openapi.json",
        "/metrics"
    ])

@dataclass
class SecurityConfig:
    """Security configuration settings."""
    secret_key: str = field(default_factory=lambda: os.getenv("CBS_SECRET_KEY", "dev-secret-change-in-production"))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_hours: int = 24
    allowed_hosts: List[str] = field(default_factory=lambda: ["*"])
    public_routes: List[str] = field(default_factory=lambda: [
        "/health",
        "/docs",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register"
    ])
    admin_routes: List[str] = field(default_factory=lambda: [
        "/api/v1/audit",
        "/api/v1/admin",
        "/encryption/key"
    ])
    password_policy: Dict[str, Any] = field(default_factory=lambda: {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special": True,
        "special_chars": "!@#$%^&*()-_=+[]{}|;:,.<>?/",
        "max_age_days": 90,
        "lockout_threshold": 5,
        "lockout_duration_minutes": 30
    })

@dataclass
class CORSConfig:
    """CORS configuration settings."""
    allow_origins: List[str] = field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    allow_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    allow_headers: List[str] = field(default_factory=lambda: [
        "Authorization", 
        "Content-Type", 
        "X-API-Key",
        "X-Encryption-Key-Id",
        "X-Request-Signature",
        "X-Client-Key",
        "X-User-Agent",
        "Accept",
        "Accept-Language",
        "Cache-Control"
    ])

@dataclass
class RateLimitingConfig:
    """Rate limiting configuration."""
    enabled: bool = True
    default_rate: int = 100  # requests per minute
    burst_size: int = 20
    window_size: int = 60  # seconds
    encrypted_bonus: float = 1.5  # Higher limits for encrypted requests
    storage_backend: str = "memory"  # memory, redis
    storage_url: Optional[str] = None
    route_limits: Dict[str, int] = field(default_factory=lambda: {
        r"/api/v1/auth/.*": 10,  # 10 requests per minute for auth endpoints
        r"/api/v1/payments/.*": 50,  # 50 requests per minute for payments
        r"/api/v1/transactions/.*": 75,  # 75 requests per minute for transactions
        r"/api/v1/accounts/.*": 100,  # 100 requests per minute for accounts
        r"/api/v1/customers/.*": 80,  # 80 requests per minute for customers
        r"/api/v1/loans/.*": 30,  # 30 requests per minute for loans
        r"/api/v1/notifications/.*": 200,  # 200 requests per minute for notifications
        r"/api/v1/audit/.*": 20,  # 20 requests per minute for audit (admin only)
    })
    user_limits: Dict[str, int] = field(default_factory=lambda: {
        "anonymous": 20,
        "customer": 100,
        "staff": 200,
        "admin": 500,
        "system": 1000
    })

@dataclass
class CacheConfig:
    """Caching configuration."""
    enabled: bool = True
    backend: str = "memory"  # memory, redis
    default_ttl: int = 300  # 5 minutes
    max_size: int = 1000  # Max cached items
    cache_url: Optional[str] = None
    cacheable_methods: List[str] = field(default_factory=lambda: ["GET"])
    cacheable_routes: List[str] = field(default_factory=lambda: [
        "/api/v1/customers",
        "/api/v1/accounts",
        "/api/v1/reference-data"
    ])
    cache_headers: List[str] = field(default_factory=lambda: [
        "Cache-Control",
        "ETag",
        "Last-Modified"
    ])

@dataclass
class LoadBalancingConfig:
    """Load balancing and circuit breaker configuration."""
    enabled: bool = True
    strategy: str = "round_robin"  # round_robin, least_connections, random
    circuit_breaker_enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    health_check_interval: int = 30  # seconds
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    retry_backoff: float = 1.0  # exponential backoff multiplier

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    enabled: bool = True
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    logging_enabled: bool = True
    log_level: str = "INFO"
    log_format: str = "json"
    metrics_endpoint: str = "/metrics"
    health_endpoint: str = "/health"
    prometheus_enabled: bool = True
    jaeger_enabled: bool = False
    jaeger_endpoint: Optional[str] = None
    log_requests: bool = True
    log_responses: bool = True
    log_sensitive_data: bool = False
    audit_enabled: bool = True
    audit_routes: List[str] = field(default_factory=lambda: [
        "/api/v1/payments",
        "/api/v1/transactions", 
        "/api/v1/accounts",
        "/api/v1/auth",
        "/api/v1/audit"
    ])

@dataclass
class ServiceConfig:
    """Service discovery and routing configuration."""
    discovery_backend: str = "static"  # static, consul, kubernetes
    discovery_url: Optional[str] = None
    services: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "account-service": {
            "url": "http://localhost:8001",
            "health_check": "/health",
            "version": "v1",
            "timeout": 30,
            "encryption_required": True
        },
        "customer-service": {
            "url": "http://localhost:8002",
            "health_check": "/health", 
            "version": "v1",
            "timeout": 30,
            "encryption_required": True
        },
        "payment-service": {
            "url": "http://localhost:8003",
            "health_check": "/health",
            "version": "v1", 
            "timeout": 30,
            "encryption_required": True
        },
        "transaction-service": {
            "url": "http://localhost:8004",
            "health_check": "/health",
            "version": "v1",
            "timeout": 30,
            "encryption_required": True
        },
        "loan-service": {
            "url": "http://localhost:8005",
            "health_check": "/health",
            "version": "v1",
            "timeout": 30,
            "encryption_required": True
        },
        "notification-service": {
            "url": "http://localhost:8006",
            "health_check": "/health",
            "version": "v1",
            "timeout": 30,
            "encryption_required": False
        },
        "audit-service": {
            "url": "http://localhost:8007",
            "health_check": "/health",
            "version": "v1",
            "timeout": 30,
            "encryption_required": True
        }
    })
    
    def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured services."""
        return self.services
    
    def get_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific service."""
        return self.services.get(service_name)

@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    debug: bool = False
    access_log: bool = True
    log_level: str = "info"

@dataclass
class SSLConfig:
    """SSL/TLS configuration."""
    enabled: bool = False
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_certs: Optional[str] = None
    verify_mode: str = "CERT_REQUIRED"
    ciphers: Optional[str] = None
    min_version: str = "TLSv1.2"
    max_version: str = "TLSv1.3"

@dataclass
class DatabaseConfig:
    """Database configuration for gateway metadata."""
    enabled: bool = False
    url: Optional[str] = None
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    encryption_enabled: bool = True

@dataclass
class GatewayConfig:
    """Main gateway configuration container."""
    environment: str = field(default_factory=lambda: os.getenv("CBS_ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("CBS_DEBUG", "false").lower() == "true")
    version: str = "2.0.0"
    
    # Component configurations
    encryption: EncryptionConfig = field(default_factory=EncryptionConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    rate_limiting: RateLimitingConfig = field(default_factory=RateLimitingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    load_balancing: LoadBalancingConfig = field(default_factory=LoadBalancingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    services: ServiceConfig = field(default_factory=ServiceConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    ssl: SSLConfig = field(default_factory=SSLConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    @classmethod
    def from_environment(cls) -> 'GatewayConfig':
        """Create configuration from environment variables."""
        config = cls()
        
        # Override with environment variables
        config.environment = os.getenv("CBS_ENVIRONMENT", config.environment)
        config.debug = os.getenv("CBS_DEBUG", str(config.debug)).lower() == "true"
        
        # Encryption config from environment
        config.encryption.enabled = os.getenv("CBS_ENCRYPTION_ENABLED", "true").lower() == "true"
        config.encryption.enforce_encryption = os.getenv("CBS_ENFORCE_ENCRYPTION", "false").lower() == "true"
        config.encryption.key_rotation_hours = int(os.getenv("CBS_KEY_ROTATION_HOURS", "24"))
        
        # Security config from environment
        config.security.access_token_expire_minutes = int(os.getenv("CBS_TOKEN_EXPIRE_MINUTES", "30"))
        config.security.refresh_token_expire_hours = int(os.getenv("CBS_REFRESH_TOKEN_EXPIRE_HOURS", "24"))
        
        # Server config from environment
        config.server.host = os.getenv("CBS_HOST", config.server.host)
        config.server.port = int(os.getenv("CBS_PORT", str(config.server.port)))
        config.server.workers = int(os.getenv("CBS_WORKERS", str(config.server.workers)))
        config.server.reload = os.getenv("CBS_RELOAD", str(config.server.reload)).lower() == "true"
        
        # SSL config from environment
        config.ssl.enabled = os.getenv("CBS_SSL_ENABLED", "false").lower() == "true"
        config.ssl.cert_file = os.getenv("CBS_SSL_CERT_FILE")
        config.ssl.key_file = os.getenv("CBS_SSL_KEY_FILE")
        
        # Rate limiting from environment
        config.rate_limiting.enabled = os.getenv("CBS_RATE_LIMITING_ENABLED", "true").lower() == "true"
        config.rate_limiting.default_rate = int(os.getenv("CBS_DEFAULT_RATE_LIMIT", "100"))
        
        # Cache config from environment
        config.cache.enabled = os.getenv("CBS_CACHE_ENABLED", "true").lower() == "true"
        config.cache.backend = os.getenv("CBS_CACHE_BACKEND", config.cache.backend)
        config.cache.cache_url = os.getenv("CBS_CACHE_URL")
        
        # Monitoring config from environment
        config.monitoring.log_level = os.getenv("CBS_LOG_LEVEL", config.monitoring.log_level)
        config.monitoring.metrics_enabled = os.getenv("CBS_METRICS_ENABLED", "true").lower() == "true"
        config.monitoring.tracing_enabled = os.getenv("CBS_TRACING_ENABLED", "true").lower() == "true"
        
        # Service URLs from environment
        for service_name in config.services.services.keys():
            env_var = f"CBS_{service_name.upper().replace('-', '_')}_URL"
            service_url = os.getenv(env_var)
            if service_url:
                config.services.services[service_name]["url"] = service_url
        
        # Production adjustments
        if config.environment == "production":
            config.debug = False
            config.server.reload = False
            config.security.allowed_hosts = [os.getenv("CBS_ALLOWED_HOSTS", "").split(",") if os.getenv("CBS_ALLOWED_HOSTS") else ["*"]][0]
            config.encryption.enforce_encryption = True
            config.ssl.enabled = True
        
        return config
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> 'GatewayConfig':
        """Load configuration from file (YAML or JSON)."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                config_data = yaml.safe_load(f)
            else:
                config_data = json.load(f)
        
        # Create base config from environment
        config = cls.from_environment()
        
        # Update with file data
        config._update_from_dict(config_data)
        
        return config
    
    def _update_from_dict(self, data: Dict[str, Any]):
        """Update configuration from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                if isinstance(getattr(self, key), (EncryptionConfig, SecurityConfig, CORSConfig, 
                                                  RateLimitingConfig, CacheConfig, LoadBalancingConfig,
                                                  MonitoringConfig, ServiceConfig, ServerConfig, 
                                                  SSLConfig, DatabaseConfig)):
                    # Update nested config object
                    nested_config = getattr(self, key)
                    for nested_key, nested_value in value.items():
                        if hasattr(nested_config, nested_key):
                            setattr(nested_config, nested_key, nested_value)
                else:
                    setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def to_yaml(self) -> str:
        """Convert configuration to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False)
    
    def save_to_file(self, config_path: Union[str, Path], format: str = "yaml"):
        """Save configuration to file."""
        config_path = Path(config_path)
        
        with open(config_path, 'w') as f:
            if format.lower() == "yaml":
                yaml.dump(self.to_dict(), f, default_flow_style=False)
            else:
                json.dump(self.to_dict(), f, indent=2, default=str)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate encryption
        if self.encryption.enabled and not self.encryption.master_key:
            issues.append("Encryption is enabled but no master key is configured")
        
        if self.encryption.enforce_encryption and not self.encryption.enabled:
            issues.append("Encryption enforcement requires encryption to be enabled")
        
        # Validate security
        if not self.security.secret_key or self.security.secret_key == "dev-secret-change-in-production":
            if self.environment == "production":
                issues.append("Production environment requires a secure secret key")
        
        if self.security.access_token_expire_minutes < 1:
            issues.append("Access token expiration must be at least 1 minute")
        
        # Validate SSL
        if self.ssl.enabled:
            if not self.ssl.cert_file or not self.ssl.key_file:
                issues.append("SSL is enabled but certificate or key file is not configured")
        
        # Validate services
        for service_name, service_config in self.services.services.items():
            if not service_config.get("url"):
                issues.append(f"Service {service_name} has no URL configured")
        
        # Validate rate limiting
        if self.rate_limiting.enabled and self.rate_limiting.default_rate < 1:
            issues.append("Rate limiting default rate must be at least 1")
        
        return issues
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ["development", "dev", "debug"]
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ["production", "prod"]
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment.lower() in ["testing", "test"]

# Default route mappings for backward compatibility
ROUTE_MAPPINGS = {
    "/api/v1/accounts": "account-service",
    "/api/v1/customers": "customer-service", 
    "/api/v1/payments": "payment-service",
    "/api/v1/transactions": "transaction-service",
    "/api/v1/loans": "loan-service",
    "/api/v1/notifications": "notification-service",
    "/api/v1/audit": "audit-service"
}

# Public routes that don't require authentication
PUBLIC_ROUTES = [
    "/health",
    "/health/detailed",
    "/docs",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh"
]

# Admin routes that require admin access
ADMIN_ROUTES = [
    "/api/v1/audit",
    "/api/v1/admin",
    "/encryption/key",
    "/metrics"
]

# Endpoint-specific rate limits
ENDPOINT_RATE_LIMITS = {
    "/api/v1/auth/login": 10,
    "/api/v1/auth/register": 5, 
    "/api/v1/payments": 50,
    "/api/v1/transactions": 75,
    "/api/v1/accounts": 100,
    "/api/v1/customers": 80,
    "/api/v1/loans": 30,
    "/api/v1/notifications": 200,
    "/api/v1/audit": 20
}

# Configuration factory functions
def create_development_config() -> GatewayConfig:
    """Create development configuration."""
    config = GatewayConfig()
    config.environment = "development"
    config.debug = True
    config.server.reload = True
    config.server.workers = 1
    config.encryption.enforce_encryption = False
    config.ssl.enabled = False
    config.monitoring.log_level = "DEBUG"
    return config

def create_production_config() -> GatewayConfig:
    """Create production configuration."""
    config = GatewayConfig.from_environment()
    config.environment = "production"
    config.debug = False
    config.server.reload = False
    config.server.workers = 4
    config.encryption.enforce_encryption = True
    config.ssl.enabled = True
    config.monitoring.log_level = "INFO"
    config.security.allowed_hosts = ["api.cbs.com", "gateway.cbs.com"]
    return config

def create_testing_config() -> GatewayConfig:
    """Create testing configuration."""
    config = GatewayConfig()
    config.environment = "testing"
    config.debug = True
    config.server.reload = False
    config.server.workers = 1
    config.encryption.enforce_encryption = False
    config.rate_limiting.enabled = False
    config.cache.enabled = False
    config.monitoring.log_level = "WARNING"
    return config

# Export main configuration class and constants
__all__ = [
    "GatewayConfig",
    "EncryptionConfig", 
    "SecurityConfig",
    "CORSConfig",
    "RateLimitingConfig",
    "CacheConfig", 
    "LoadBalancingConfig",
    "MonitoringConfig",
    "ServiceConfig",
    "ServerConfig",
    "SSLConfig",
    "DatabaseConfig",
    "ROUTE_MAPPINGS",
    "PUBLIC_ROUTES", 
    "ADMIN_ROUTES",
    "ENDPOINT_RATE_LIMITS",
    "create_development_config",
    "create_production_config", 
    "create_testing_config"
]
