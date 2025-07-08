"""
Configuration Management System
Centralized configuration loading and management for all services
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration"""
    engine: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    database: str = "cbs_platform"
    username: str = "postgres"
    password: str = "password"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    
    @property
    def url(self) -> str:
        """Get database URL"""
        return f"{self.engine}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    database: int = 0
    decode_responses: bool = True
    socket_keepalive: bool = True
    max_connections: int = 50
    
    @property
    def url(self) -> str:
        """Get Redis URL"""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.database}"


@dataclass
class KafkaConfig:
    """Kafka configuration"""
    bootstrap_servers: list = field(default_factory=lambda: ["localhost:9092"])
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = True
    group_id: str = "cbs-platform"
    value_deserializer: str = "json"
    value_serializer: str = "json"
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_hash_algorithm: str = "argon2"
    allowed_hosts: list = field(default_factory=lambda: ["*"])


@dataclass
class APIConfig:
    """API configuration"""
    title: str = "CBS Platform API"
    description: str = "Core Banking System API"
    version: str = "2.0.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    debug: bool = False
    reload: bool = False


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    metrics_enabled: bool = True
    metrics_endpoint: str = "/metrics"
    health_check_enabled: bool = True
    health_check_endpoint: str = "/health"
    tracing_enabled: bool = True
    service_name: str = "cbs-platform"
    jaeger_endpoint: str = "http://localhost:14268/api/traces"


@dataclass
class CORSConfig:
    """CORS configuration"""
    allow_origins: list = field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    allow_methods: list = field(default_factory=lambda: ["*"])
    allow_headers: list = field(default_factory=lambda: ["*"])


@dataclass
class RateLimitingConfig:
    """Rate limiting configuration"""
    enabled: bool = True
    default_rate: str = "100/minute"
    burst_rate: str = "50/minute"
    storage_url: str = "redis://localhost:6379"


@dataclass
class ServiceConfig:
    """Individual service configuration"""
    url: str
    health_check: str = "/health"
    timeout: int = 30
    retries: int = 3


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    file: Optional[str] = None


@dataclass
class FeatureFlags:
    """Feature flags configuration"""
    enable_registration: bool = True
    enable_2fa: bool = True
    enable_push_notifications: bool = True
    enable_analytics: bool = True
    enable_ml_fraud_detection: bool = False


@dataclass
class AppConfig:
    """Main application configuration"""
    app_name: str = "CBS Platform"
    app_version: str = "2.0.0"
    environment: str = "development"
    debug: bool = False
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    kafka: KafkaConfig = field(default_factory=KafkaConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    api: APIConfig = field(default_factory=APIConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    rate_limiting: RateLimitingConfig = field(default_factory=RateLimitingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    services: Dict[str, ServiceConfig] = field(default_factory=dict)


class ConfigManager:
    """Configuration manager for loading and managing application configuration"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent / "config"
        self._config_cache: Dict[str, AppConfig] = {}
    
    def load_config(self, environment: str = None) -> AppConfig:
        """Load configuration for specified environment"""
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development")
        
        # Check cache first
        if environment in self._config_cache:
            return self._config_cache[environment]
        
        logger.info(f"Loading configuration for environment: {environment}")
        
        # Load base configuration
        base_config = self._load_yaml_file("base.yaml")
        
        # Load environment-specific configuration
        env_config = {}
        env_file = f"{environment}.yaml"
        if (self.config_dir / env_file).exists():
            env_config = self._load_yaml_file(env_file)
        
        # Merge configurations
        merged_config = self._merge_configs(base_config, env_config)
        
        # Apply environment variable overrides
        merged_config = self._apply_env_overrides(merged_config)
        
        # Create configuration object
        config = self._create_config_object(merged_config, environment)
        
        # Cache configuration
        self._config_cache[environment] = config
        
        logger.info(f"Configuration loaded successfully for environment: {environment}")
        return config
    
    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            logger.warning(f"Configuration file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # Replace environment variables
                content = os.path.expandvars(content)
                return yaml.safe_load(content) or {}
        except Exception as e:
            logger.error(f"Error loading configuration file {file_path}: {str(e)}")
            return {}
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        # Common environment variable mappings
        env_mappings = {
            "DATABASE_URL": ("database", "url"),
            "DATABASE_HOST": ("database", "host"),
            "DATABASE_PORT": ("database", "port"),
            "DATABASE_NAME": ("database", "database"),
            "DATABASE_USER": ("database", "username"),
            "DATABASE_PASSWORD": ("database", "password"),
            "REDIS_URL": ("redis", "url"),
            "REDIS_HOST": ("redis", "host"),
            "REDIS_PORT": ("redis", "port"),
            "REDIS_PASSWORD": ("redis", "password"),
            "JWT_SECRET_KEY": ("security", "secret_key"),
            "KAFKA_BOOTSTRAP_SERVERS": ("kafka", "bootstrap_servers"),
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # Navigate to the config section
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Set the value, handle special cases
                final_key = config_path[-1]
                if env_var == "KAFKA_BOOTSTRAP_SERVERS":
                    current[final_key] = env_value.split(",")
                elif env_var in ["DATABASE_PORT", "REDIS_PORT"]:
                    current[final_key] = int(env_value)
                else:
                    current[final_key] = env_value
        
        return config
    
    def _create_config_object(self, config_dict: Dict[str, Any], environment: str) -> AppConfig:
        """Create configuration object from dictionary"""
        
        # Extract main app config
        app_data = config_dict.get("app", {})
        app_config = AppConfig(
            app_name=app_data.get("name", "CBS Platform"),
            app_version=app_data.get("version", "2.0.0"),
            environment=environment,
            debug=environment == "development"
        )
        
        # Database config
        db_data = config_dict.get("database", {})
        app_config.database = DatabaseConfig(
            engine=db_data.get("engine", "postgresql"),
            host=db_data.get("host", "localhost"),
            port=db_data.get("port", 5432),
            database=db_data.get("database", "cbs_platform"),
            username=db_data.get("username", "postgres"),
            password=db_data.get("password", "password"),
            pool_size=db_data.get("pool_size", 10),
            max_overflow=db_data.get("max_overflow", 20),
            pool_timeout=db_data.get("pool_timeout", 30),
            pool_recycle=db_data.get("pool_recycle", 3600),
            echo=db_data.get("echo", False)
        )
        
        # Redis config
        redis_data = config_dict.get("redis", {})
        app_config.redis = RedisConfig(
            host=redis_data.get("host", "localhost"),
            port=redis_data.get("port", 6379),
            password=redis_data.get("password"),
            database=redis_data.get("database", 0),
            decode_responses=redis_data.get("decode_responses", True),
            socket_keepalive=redis_data.get("socket_keepalive", True),
            max_connections=redis_data.get("max_connections", 50)
        )
        
        # Kafka config
        kafka_data = config_dict.get("kafka", {})
        app_config.kafka = KafkaConfig(
            bootstrap_servers=kafka_data.get("bootstrap_servers", ["localhost:9092"]),
            auto_offset_reset=kafka_data.get("auto_offset_reset", "earliest"),
            enable_auto_commit=kafka_data.get("enable_auto_commit", True),
            group_id=kafka_data.get("group_id", "cbs-platform"),
            security_protocol=kafka_data.get("security_protocol", "PLAINTEXT"),
            sasl_mechanism=kafka_data.get("sasl_mechanism")
        )
        
        # Security config
        security_data = config_dict.get("security", {})
        app_config.security = SecurityConfig(
            secret_key=security_data.get("secret_key", "your-secret-key-here"),
            algorithm=security_data.get("algorithm", "HS256"),
            access_token_expire_minutes=security_data.get("access_token_expire_minutes", 30),
            refresh_token_expire_days=security_data.get("refresh_token_expire_days", 7),
            password_hash_algorithm=security_data.get("password_hash_algorithm", "argon2"),
            allowed_hosts=security_data.get("allowed_hosts", ["*"])
        )
        
        # Services config
        services_data = config_dict.get("services", {})
        app_config.services = {}
        for service_name, service_data in services_data.items():
            app_config.services[service_name] = ServiceConfig(
                url=service_data["url"],
                health_check=service_data.get("health_check", "/health"),
                timeout=service_data.get("timeout", 30),
                retries=service_data.get("retries", 3)
            )
        
        # Feature flags
        features_data = config_dict.get("features", {})
        app_config.features = FeatureFlags(
            enable_registration=features_data.get("enable_registration", True),
            enable_2fa=features_data.get("enable_2fa", True),
            enable_push_notifications=features_data.get("enable_push_notifications", True),
            enable_analytics=features_data.get("enable_analytics", True),
            enable_ml_fraud_detection=features_data.get("enable_ml_fraud_detection", False)
        )
        
        return app_config
    
    def reload_config(self, environment: str = None) -> AppConfig:
        """Reload configuration by clearing cache and loading again"""
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development")
        
        # Clear cache
        if environment in self._config_cache:
            del self._config_cache[environment]
        
        return self.load_config(environment)


# Global configuration manager instance
config_manager = ConfigManager()

def get_config(environment: str = None) -> AppConfig:
    """Get application configuration"""
    return config_manager.load_config(environment)
