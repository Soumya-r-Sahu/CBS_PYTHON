# Environment Implementation Guide

## Overview

This guide outlines how to implement environment awareness in all modules of the Core Banking System. The system supports three primary environments:

- **Development** (🔵): For development and debugging
- **Test** (🟡): For QA and testing
- **Production** (🟢): For live operations

## 1. Environment Detection Pattern

### Import the Environment Module
```python
# Import the environment module
try:
    from app.config.environment import (
        Environment, get_environment_name, is_production, is_development, is_test,
        is_debug_enabled, get_debug_level, env_aware
    )
except ImportError:
    # Fallback environment detection
    import os
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    
    def is_production(): return env_str == "production"
    def is_development(): return env_str == "development"
    def is_test(): return env_str == "test"
    def get_environment_name(): return env_str.capitalize()
    def is_debug_enabled(): return os.environ.get("CBS_DEBUG", "false").lower() == "true"
    def get_debug_level(): return int(os.environ.get("CBS_DEBUG_LEVEL", "0"))
    
    class Environment:
        DEVELOPMENT = "development"
        TEST = "test"
        PRODUCTION = "production"
        
    def env_aware(prod=None, dev=None, test=None):
        """Return value based on current environment"""
        if is_production() and prod is not None:
            return prod
        elif is_development() and dev is not None:
            return dev
        elif is_test() and test is not None:
            return test
        # Default fallbacks
        if is_production():
            return test if prod is None else prod
        elif is_development():
            return dev if dev is not None else (test if test is not None else prod)
        else:  # test
            return test if test is not None else (dev if dev is not None else prod)
```

### Apply in Class Constructor
```python
def __init__(self):
    # Environment-specific settings
    self.env_name = get_environment_name()
    
    # Set environment-specific colors
    if is_production():
        self.env_color = Fore.GREEN
        # Production-specific settings
    elif is_test():
        self.env_color = Fore.YELLOW
        # Test-specific settings
    else:  # development
        self.env_color = Fore.BLUE
        # Development-specific settings
```

## 2. UI Elements Pattern

### Environment Banner Template
```python
def show_environment_banner(self):
    """Display environment banner with appropriate styling"""
    env_banner = f"""
{self.env_color}╔════════════════════════════════════════════════════╗
║ MODULE NAME                                       ║
║ Environment: {self.env_name.ljust(20)}                   ║
╚════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(env_banner)
```

### Environment Info Display
```python
def show_environment_info(self):
    """Display detailed environment information"""
    print(f"\n{self.env_color}===== Environment Information ====={Style.RESET_ALL}")
    print(f"Environment: {self.env_color}{self.env_name}{Style.RESET_ALL}")
    print(f"Debug Mode: {'Enabled' if is_debug_enabled() else 'Disabled'}")
    
    # Environment-specific behaviors
    print("\nEnvironment-specific behaviors:")
    if is_test():
        print(f"{Fore.YELLOW}• Test limitations and behaviors{Style.RESET_ALL}")
    elif is_development():
        print(f"{Fore.BLUE}• Development features{Style.RESET_ALL}")
    else:  # Production
        print(f"{Fore.GREEN}• Production settings{Style.RESET_ALL}")
    
    input("\nPress Enter to continue...")
```

## 3. Database Access Pattern

### Table Prefixing
```python
def get_table_name(base_name):
    """Get environment-specific table name"""
    if not is_production():
        return f"{get_environment_name().lower()}_{base_name}"
    return base_name
```

### Connection Pooling
```python
def create_connection_pool():
    """Create environment-specific connection pool"""
    if is_production():
        return {
            'pool_size': 20,
            'pool_recycle': 3600,
            'pool_timeout': 30,
            'max_overflow': 10
        }
    elif is_test():
        return {
            'pool_size': 5,
            'pool_recycle': 300,
            'pool_timeout': 30,
            'max_overflow': 3
        }
    else:  # development
        return {
            'pool_size': 3,
            'pool_recycle': 300,
            'pool_timeout': 30,
            'max_overflow': 2
        }
```

## 4. Business Logic Pattern

### Environment-Specific Limits
```python
def get_transaction_limits():
    """Get environment-specific transaction limits"""
    if is_production():
        return {
            'daily_limit': 100000,
            'transaction_limit': 50000,
            'min_amount': 1
        }
    elif is_test():
        return {
            'daily_limit': 50000,
            'transaction_limit': 25000,
            'min_amount': 1
        }
    else:  # development
        return {
            'daily_limit': 10000,
            'transaction_limit': 5000,
            'min_amount': 1
        }
```

### Safety Checks
```python
def validate_cross_environment_operation(source_env, target_env, operation_type):
    """Validate operations between environments"""
    if source_env != target_env:
        if source_env != "production" and target_env == "production":
            raise ValueError(f"Cannot perform {operation_type} from {source_env} to production")
        if source_env == "production" and target_env != "production":
            # This may be allowed in specific cases with explicit override
            if not os.environ.get("CBS_ALLOW_PROD_TO_NONPROD", "false").lower() == "true":
                raise ValueError(f"Cannot perform {operation_type} from production to {target_env}")
```

## 5. Logging Pattern

### Environment-Specific Logging
```python
def setup_logging():
    """Configure environment-specific logging"""
    log_level = env_aware(
        prod=logging.WARNING,
        dev=logging.DEBUG,
        test=logging.INFO
    )
    
    log_format = env_aware(
        prod='%(asctime)s [%(levelname)s] %(message)s',
        dev='%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
        test='%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s'
    )
    
    log_dir = f"logs/{get_environment_name().lower()}"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(f"{log_dir}/cbs.log"),
            logging.StreamHandler()
        ]
    )
```

## 6. Module Integration Checklist

For each module that needs environment awareness, implement the following:

1. **Import Environment Module**
   - Add the standard import pattern at the top of the file
   - Include fallback environment detection

2. **Update Constructor**
   - Add environment name, color, and settings
   - Set environment-specific behavior flags

3. **Add Visual Indicators**
   - Implement environment banner in UI
   - Add color coding to terminal output
   - Show/hide debug options based on environment

4. **Implement Data Isolation**
   - Use table prefixing for database tables
   - Use environment-specific directories for file storage
   - Implement environment-specific connection settings

5. **Add Business Logic Constraints**
   - Set appropriate limits based on environment
   - Implement environment-specific validation rules
   - Add safety checks for cross-environment operations

6. **Configure Environment-Specific Logging**
   - Set log levels based on environment
   - Use environment-specific log directories
   - Add detailed logging in non-production environments

## 7. API Endpoints

### Environment Information Endpoint
```python
@app.route('/api/environment')
def get_environment_info():
    """API endpoint to return environment information"""
    if is_production():
        # Limited info in production for security
        return {
            "environment": "production",
            "status": "active",
            "version": get_app_version()
        }
    else:
        # Detailed info in non-production
        return {
            "environment": get_environment_name().lower(),
            "status": "active",
            "debug": is_debug_enabled(),
            "debug_level": get_debug_level(),
            "config_path": os.environ.get("CBS_CONFIG_PATH", "default"),
            "version": get_app_version(),
            "database": {
                "name": f"{get_environment_name().lower()}_db",
                "table_prefix": get_environment_name().lower() + "_"
            }
        }
```

## 8. API Headers

### Include Environment Information
```python
@app.after_request
def add_environment_headers(response):
    """Add environment information to API responses"""
    response.headers['X-CBS-Environment'] = get_environment_name()
    if not is_production():
        response.headers['X-CBS-Debug'] = str(is_debug_enabled()).lower()
    return response
```

## 9. Environment-Specific Testing

### Test Features Pattern
```python
def test_feature():
    """Test with environment-specific expectations"""
    if is_production():
        # Production expectations
        assert feature.max_limit == 100000
    elif is_test():
        # Test environment expectations
        assert feature.max_limit == 50000
    else:
        # Development expectations
        assert feature.max_limit == 10000
```

## 10. Deployment Script Integration

### Environment-Specific Deployment
```python
def deploy(target_env):
    """Deploy with environment-specific steps"""
    if target_env == "production":
        # Production deployment steps
        run_security_checks()
        require_approval()
        backup_database()
        deploy_with_zero_downtime()
    elif target_env == "test":
        # Test deployment steps
        backup_database()
        reset_test_data()
        deploy_standard()
    else:
        # Development deployment
        deploy_standard()
```

## 11. Environment Validation

### Validate Configuration
```python
def validate_environment_config():
    """Validate environment configuration is correct"""
    env = get_environment_name().lower()
    
    # Check if required environment variables are set
    required_vars = env_aware(
        prod=["CBS_DB_PASSWORD", "CBS_SECRET_KEY", "CBS_API_KEY"],
        test=["CBS_DB_PASSWORD"],
        dev=[]
    )
    
    missing = [var for var in required_vars if var not in os.environ]
    if missing:
        raise ValueError(f"Missing required environment variables for {env}: {', '.join(missing)}")
    
    # Validate database connection
    try:
        db = get_database_connection()
        db.execute("SELECT 1")
    except Exception as e:
        raise ValueError(f"Database connection failed in {env}: {str(e)}")
```

## Implementation Timeline

1. **Phase 1: Core Components** (Completed)
   - Environment detection module
   - Database connection
   - Configuration system
   - Logging system
   - ATM interface
   - Admin panel
   - UPI services
   - Transaction processor

2. **Phase 2: Additional Components** (1-2 weeks)
   - Customer dashboard
   - Netbanking services
   - Employee interfaces
   - Report generation
   - Notification services

3. **Phase 3: API and Integration** (2-3 weeks)
   - RESTful API endpoints
   - Partner system integrations
   - Mobile app services
   - External payment gateways

4. **Phase 4: Testing and Monitoring** (1-2 weeks)
   - Environment-specific test suites
   - Performance monitoring
   - Security validation
   - Compliance checking

## Resources

- [Environment Module Documentation](../app/config/environment.py)
- [Test Configuration Reference](../tests/environment_test_config.py)
- [Deployment Scripts](../scripts/deployment/deploy_environment.py)
- [Environment Show Script](../scripts/show_environment.py)
