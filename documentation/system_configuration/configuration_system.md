# Configuration System

This document provides an overview of the centralized configuration system used in the CBS_PYTHON project.

## Architecture Overview

The CBS_PYTHON configuration system follows a hierarchical approach that allows for flexible configuration across different environments while maintaining security and separation of concerns.

## Key Components

### 1. Configuration Manager

The `ConfigManager` class in `config.py` serves as the central point for all configuration access:

```python
from config import ConfigManager

# Get configuration instance
config = ConfigManager.get_instance()

# Access configuration values
database_url = config.get("database.url")
log_level = config.get("logging.level", default="INFO")
```

### 2. Configuration Sources

The system loads configuration from multiple sources in the following order:

1. **System defaults** (hardcoded in code)
2. **Configuration files** (YAML-based)
3. **Environment variables**
4. **Command-line arguments**

### 3. Configuration Files

Configuration files are structured YAML documents:

```
config/
├── defaults.yaml           # Base configuration for all environments
├── development.yaml        # Development-specific configuration
├── test.yaml               # Test environment configuration
├── production.yaml         # Production configuration
└── local.yaml              # Local developer overrides (git-ignored)
```

### 4. Secret Management

Sensitive configuration values (passwords, API keys, etc.) are handled separately:

1. **Environment variables**: Primary method for production secrets
2. **Secret files**: For development convenience
3. **Secure vault integration**: For advanced deployments

## Configuration Loading Process

1. **Initialization**: `ConfigManager` initializes during application startup
2. **Environment Detection**: System determines the current environment
3. **Base Configuration**: Loads default configuration from `defaults.yaml`
4. **Environment Configuration**: Loads environment-specific configuration
5. **Environment Variables**: Overrides values from environment variables
6. **Command-line Arguments**: Applies command-line arguments
7. **Validation**: Validates all required configuration values

## Usage Examples

### Basic Configuration Access

```python
from config import ConfigManager

config = ConfigManager.get_instance()

# Simple access
db_type = config.get("database.type")

# With default value
port = config.get("api.port", default=8000)

# Typed access
debug_mode = config.get_bool("logging.debug", default=False)
connection_timeout = config.get_int("database.timeout", default=30)
```

### Accessing Nested Configuration

```python
# Accessing nested configuration
smtp_config = config.get_section("notifications.email.smtp")
host = smtp_config.get("host")
port = smtp_config.get_int("port")

# Alternatively, use dot notation
smtp_host = config.get("notifications.email.smtp.host")
```

### Environment-specific Access

```python
# Get configuration based on current environment
if config.is_development():
    # Development-specific logic
    pass
elif config.is_production():
    # Production-specific logic
    pass

# Get environment name
env_name = config.get_environment()
```

## Configuration Updates

The configuration is generally loaded once at application startup. However, there are cases where it needs to be reloaded:

```python
# Reload configuration (e.g., after changes to config files)
config.reload()

# Force a specific environment
config.reload(environment="test")
```

## Custom Configuration Properties

The system allows defining custom properties with transformations:

```python
# Define a custom property with transformation
@config.property("database.url")
def get_database_url(config):
    db_type = config.get("database.type")
    if db_type == "sqlite":
        return f"sqlite:///{config.get('database.name')}"
    else:
        return (f"{db_type}://{config.get('database.user')}:"
                f"{config.get('database.password')}@"
                f"{config.get('database.host')}:"
                f"{config.get('database.port')}/"
                f"{config.get('database.name')}")
```

## Configuration Validation

The system validates configuration at startup:

```python
# Define configuration schema
config.define_schema({
    "database": {
        "type": {"type": "string", "required": True},
        "name": {"type": "string", "required": True},
        "host": {"type": "string", "required_if": {"database.type": ["postgresql", "mysql"]}},
        "port": {"type": "integer", "required_if": {"database.type": ["postgresql", "mysql"]}},
        "user": {"type": "string", "required_if": {"database.type": ["postgresql", "mysql"]}},
        "password": {"type": "string", "required_if": {"database.type": ["postgresql", "mysql"]}}
    }
})

# Validate configuration
validation_errors = config.validate()
if validation_errors:
    raise ConfigurationError(f"Invalid configuration: {validation_errors}")
```

## Working with Secrets

Secrets should never be hardcoded or stored in version control:

```python
# INCORRECT - Do not do this!
API_KEY = "1234567890abcdef"

# CORRECT - Load from configuration system
api_key = config.get("integrations.payment_gateway.api_key")
```

For local development, create a `local.yaml` file (git-ignored):

```yaml
# local.yaml - DO NOT COMMIT THIS FILE
integrations:
  payment_gateway:
    api_key: "1234567890abcdef"  # Development API key
```

## Configuration for Tests

For testing, you can create test-specific configurations:

```python
# In tests
from config import ConfigManager

def test_feature():
    # Create test-specific configuration
    test_config = ConfigManager.create_test_instance({
        "feature": {
            "enabled": True,
            "timeout": 5
        }
    })
    
    # Run test with custom configuration
    with ConfigManager.use_instance(test_config):
        # Your test code here
        pass
```

## Best Practices

1. **Centralize Configuration Access**: Always use the `ConfigManager` to access configuration
2. **Default Values**: Provide sensible defaults for non-critical configuration
3. **Environment Variables**: Use environment variables for secrets and environment-specific values
4. **Configuration Comments**: Document configuration options in YAML files
5. **Validation**: Validate configuration at startup to fail fast
6. **Minimal Scope**: Only access configuration values where needed, don't pass around the config object
7. **Testing**: Make configuration easily overridable for testing

## Troubleshooting

### Common Issues

1. **Missing Configuration**: Configuration value is not found
   - Check if the key exists in the appropriate configuration file
   - Verify the correct environment is being used
   - Check for typos in the configuration key

2. **Type Errors**: Wrong type for configuration value
   - Use type-specific getters (get_int, get_bool, etc.)
   - Validate configuration schema at startup

3. **Environment Variables Not Applied**
   - Ensure environment variables are prefixed with `CBS_`
   - Check for capitalization and format (use uppercase for env vars)

### Debugging Tips

1. **Dump Configuration**: 
   ```python
   print(config.dump())  # Print the entire configuration
   ```

2. **Check Configuration Source**:
   ```python
   source = config.get_value_source("database.url")
   print(f"Config value loaded from: {source}")  # E.g., "env_var", "yaml_file", "default"
   ```

3. **Enable Debug Logging**:
   ```
   export CBS_LOG_LEVEL=DEBUG
   ```

## Related Documentation

- [Environment-Specific Configurations](environment_configs.md)
- [Security Configurations](security_configurations.md)
- [Database Configuration](database_configuration.md)