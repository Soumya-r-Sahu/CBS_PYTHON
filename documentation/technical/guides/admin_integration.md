# Admin Module Integration Guide 🛠️

This guide provides instructions for integrating a new module with the Admin module in CBS_PYTHON.

## Key Steps 📋

1. **Implement Module Registry Interface**: Define module-specific information.
2. **Extend Base Module Registry**: Use the base implementation for common methods.
3. **Register with Admin Module**: Use the Admin Integration Client.
4. **Monitor Health**: Implement health checks for your module.
5. **Handle Config Updates**: Apply configuration changes dynamically.

_Last updated: May 23, 2025_

## Overview

This document describes how to integrate a new module with the Admin module in the CBS_PYTHON system. The Admin module provides centralized control, configuration, and monitoring capabilities for all modules in the system.

## Integration Architecture

The integration between the Admin module and other modules is based on the following components:

1. **Module Registry Interface**: Defines the standard interface that all modules must implement to register with the Admin module.
2. **Base Module Registry**: Provides a base implementation of the Module Registry Interface that modules can extend.
3. **Admin Integration Client**: Provides a unified way for modules to communicate with the Admin module.
4. **Module Registry Implementations**: Module-specific implementations of the Module Registry Interface.
5. **Health Monitoring Services**: Collect health metrics from all modules and report them to the Admin module.
6. **Configuration Updater Service**: Propagates configuration changes from the Admin module to modules.

## Integration Process

### 1. Implement the Module Registry Interface

To integrate a new module with the Admin module, you need to create a module-specific implementation of the Module Registry Interface. This interface is defined in `integration_interfaces/api/module_registry.py`.

The interface requires implementing the following methods:

- `get_module_info()`: Returns basic information about the module (ID, name, version, etc.).
- `get_api_endpoints()`: Returns a list of API endpoints exposed by the module.
- `get_feature_flags()`: Returns a list of feature flags defined by the module.
- `get_configurations()`: Returns a list of configurable settings for the module.
- `health_check()`: Performs a health check for the module and returns the results.

### 2. Extend the Base Module Registry

Instead of implementing the Module Registry Interface from scratch, you can extend the Base Module Registry provided in `integration_interfaces/api/base_module_registry.py`. This class provides default implementations for many of the required methods.

Example:

```python
from integration_interfaces.api.base_module_registry import BaseModuleRegistry

class MyModuleRegistry(BaseModuleRegistry):
    def __init__(self):
        super().__init__(
            module_id="my_module",
            module_name="My Module",
            version="1.0.0",
            description="My module provides these services..."
        )
        self.set_dependencies(["core_banking"])

    # Override other methods as needed...
```

### 3. Define Module-Specific Information

Implement the methods of the Module Registry Interface to provide module-specific information:

- `get_api_endpoints()`: List all REST API endpoints exposed by your module.
- `get_feature_flags()`: List all feature flags defined by your module.
- `get_configurations()`: List all configurable settings for your module.
- `health_check()`: Implement a health check that monitors the health of your module.

### 4. Register with the Admin Module

Use the Admin Integration Client to register your module with the Admin module:

```python
from integration_interfaces.api.admin_client import AdminIntegrationClient

def register_with_admin():
    registry = MyModuleRegistry()
    client = AdminIntegrationClient(
        module_id=registry.module_id,
        api_key="your-api-key"
    )

    client.register_module(registry.get_module_info())
    client.register_api_endpoints(registry.get_api_endpoints())
    client.register_feature_flags(registry.get_feature_flags())
    client.register_configurations(registry.get_configurations())
    client.send_health_metrics(registry.health_check())
```

### 5. Implement Health Monitoring

Implement the `health_check()` method to monitor the health of your module:

```python
def health_check(self) -> Dict[str, Any]:
    # Get CPU and memory usage
    process = psutil.Process(os.getpid())
    cpu_percent = process.cpu_percent(interval=0.1)
    memory_info = process.memory_info()
    memory_percent = process.memory_percent()

    # Check dependencies and services
    # ...

    return {
        "status": "healthy",  # or "warning", "critical", "unknown"
        "metrics": {
            "cpu_percent": cpu_percent,
            "memory_bytes": memory_info.rss,
            "memory_percent": memory_percent
        },
        "details": {
            # Additional details...
        },
        "alerts": []  # List of alert messages if any
    }
```

### 6. Handle Configuration Updates

Your module should be able to receive and apply configuration updates from the Admin module. This typically involves:

1. Implementing a configuration update endpoint in your module's API.
2. Subscribing to configuration changes from the Admin module.
3. Applying configuration changes to your module's runtime configuration.

## API Key Authentication

All communication between modules and the Admin module requires API key authentication. Each module should have a unique API key that is used to authenticate with the Admin module.

API keys are managed by the Admin module's API Key Manager service. To obtain an API key for your module, contact the system administrator.

## Health Monitoring Service

The Health Monitoring Service periodically collects health metrics from all registered modules and reports them to the Admin module. The service:

1. Checks the health of each module at regular intervals.
2. Analyzes health trends to detect potential issues.
3. Sends alerts when issues are detected.

## Configuration Updater Service

The Configuration Updater Service propagates configuration changes from the Admin module to all registered modules. The service:

1. Polls the Admin module for configuration changes.
2. Applies configuration changes to the respective modules.
3. Notifies modules about configuration changes.

## Example: Integrating a New Module

Here's a complete example of integrating a new module with the Admin module:

1. Create a new file `my_module/admin_integration.py`:

```python
import os
import sys
import logging
import psutil
from datetime import datetime

# Add the parent directory to sys.path to import the integration interfaces
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from integration_interfaces.api.base_module_registry import BaseModuleRegistry
from integration_interfaces.api.admin_client import AdminIntegrationClient

logger = logging.getLogger(__name__)

class MyModuleRegistry(BaseModuleRegistry):
    def __init__(self):
        super().__init__(
            module_id="my_module",
            module_name="My Module",
            version="1.0.0",
            description="My module provides these services..."
        )
        self.set_dependencies(["core_banking"])

    def get_api_endpoints(self):
        return [
            {
                "path": "/api/v1/my_module/resource",
                "method": "GET",
                "description": "Get a resource",
                "auth_required": True,
                "rate_limit": 100
            },
            # More endpoints...
        ]

    def get_feature_flags(self):
        return [
            {
                "name": "enable_feature_x",
                "description": "Enable Feature X",
                "enabled": True,
                "affects_endpoints": [
                    "/api/v1/my_module/resource"
                ]
            },
            # More feature flags...
        ]

    def get_configurations(self):
        return [
            {
                "key": "setting_a",
                "value": "default_value",
                "type": "module",
                "description": "Setting A description",
                "is_sensitive": False,
                "allowed_values": None
            },
            # More configurations...
        ]

    def health_check(self):
        process = psutil.Process(os.getpid())
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()

        return {
            "status": "healthy",
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_bytes": memory_info.rss,
                "memory_percent": memory_percent
            },
            "details": {
                "uptime": "12:34:56"  # Mock value
            },
            "alerts": []
        }

def register_with_admin():
    try:
        registry = MyModuleRegistry()
        client = AdminIntegrationClient(
            module_id=registry.module_id,
            api_key="your-api-key"
        )

        client.register_module(registry.get_module_info())
        client.register_api_endpoints(registry.get_api_endpoints())
        client.register_feature_flags(registry.get_feature_flags())
        client.register_configurations(registry.get_configurations())
        client.send_health_metrics(registry.health_check())

        logger.info(f"Successfully registered {registry.module_name} with Admin module")
        return True

    except Exception as e:
        logger.error(f"Failed to register with Admin module: {str(e)}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if register_with_admin():
        print("Successfully registered My Module with Admin module")
    else:
        print("Failed to register My Module with Admin module")
        sys.exit(1)
```

2. Add your module to the central registration script (`register_modules.py`).

3. Run the registration script to register your module with the Admin module.

## Troubleshooting

### Registration Fails

If registration fails, check the following:

- Make sure the Admin module is running and accessible.
- Check that you're using the correct API key.
- Verify that your module's dependencies are registered first.
- Check the logs for specific error messages.

### Health Check Fails

If health checks are failing, check the following:

- Make sure your module's health check implementation is correct.
- Check for resource constraints (CPU, memory, disk space).
- Verify that all dependencies and services are available.
- Check the logs for specific error messages.

### Configuration Updates Not Applied

If configuration updates are not being applied, check the following:

- Make sure your module is correctly registered with the Admin module.
- Check that your module's configuration update endpoint is implemented and working.
- Verify that the Configuration Updater Service is running.
- Check the logs for specific error messages.

## Best Practices

1. **Keep Health Checks Lightweight**: Health checks should be fast and non-intrusive.
2. **Use Feature Flags**: Use feature flags to control the visibility and functionality of features.
3. **Define Meaningful Configurations**: Define configurations that provide real value to administrators.
4. **Set Dependencies Correctly**: Make sure your module's dependencies are set correctly.
5. **Handle API Key Rotation**: Be prepared to handle API key rotation for security purposes.
6. **Monitor Health Trends**: Look for trends in health metrics to identify potential issues before they become critical.
7. **Document Your Module's API**: Provide documentation for your module's API endpoints.

## References

- [Module Registry Interface](/integration_interfaces/api/module_registry.py)
- [Base Module Registry](/integration_interfaces/api/base_module_registry.py)
- [Admin Integration Client](/integration_interfaces/api/admin_client.py)
- [Health Check Service](/monitoring/health_check_service.py)
- [Configuration Updater Service](/app/Portals/Admin/dashboard/services/config_updater.py)
