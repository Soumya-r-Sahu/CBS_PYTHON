"""
CBS Module Registration

This script registers all CBS modules with the Admin dashboard and the service registry.
It collects module information, API endpoints, feature flags, 
and configurations from each module and sends them to the Admin module.

Author: cbs-core-dev
Version: 1.1.2
"""
import os
import sys
import logging
import importlib
import argparse
from typing import List, Dict, Any, Optional
import time

# Import module interface
from utils.lib.module_interface import ModuleInterface
from utils.lib.service_registry import ServiceRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# List of modules to register
# The order is important - modules should be registered in dependency order
MODULES = [
    "core_banking",        # Core banking should be registered first as other modules depend on it
    "payments",            # Payments module depends on core_banking
    "digital_channels",    # Digital channels depend on core_banking and payments
    "risk_compliance",     # Risk & compliance depends on core_banking and payments
    "treasury",            # Treasury depends on core_banking and payments
    "crm",                 # Customer Relationship Management
    "hr_erp",              # Human Resources and ERP
    # Add new modules here in the appropriate order
]

def register_module(module_name: str, admin_url: str = None, api_key: str = None) -> bool:
    """
    Register a module with the Admin dashboard and service registry.
    
    Args:
        module_name: Name of the module to register
        admin_url: URL of the Admin module API
        api_key: API key for authentication
        
    Returns:
        True if registration was successful, False otherwise
    """
    try:
        # Set environment variables if provided
        if admin_url:
            os.environ["CBS_ADMIN_BASE_URL"] = admin_url
        if api_key:
            os.environ["CBS_ADMIN_API_KEY"] = api_key
            
        # Register with service registry if module implements the interface
        registry_result = register_with_service_registry(module_name)
        
        # Register with admin if module has admin_integration
        admin_result = register_with_admin(module_name)
        
        # Consider registration successful if either succeeds
        return registry_result or admin_result
    
    except Exception as e:
        logger.error(f"Error registering {module_name}: {str(e)}")
        return False


def register_with_admin(module_name: str) -> bool:
    """
    Register a module with the Admin dashboard.
    
    Args:
        module_name: Name of the module to register
        
    Returns:
        True if registration was successful, False otherwise
    """
    try:
        # Import the module's admin_integration module
        module_path = f"{module_name}.admin_integration"
        
        try:
            module = importlib.import_module(module_path)
            
            # Call the register_with_admin function
            if hasattr(module, "register_with_admin"):
                result = module.register_with_admin()
                if result:
                    logger.info(f"Successfully registered {module_name} with Admin module")
                    return True
                else:
                    logger.error(f"Failed to register {module_name} with Admin module")
                    return False
            else:
                logger.warning(f"Module {module_name} does not have a register_with_admin function")
                return False
        except ImportError:
            logger.warning(f"Module {module_name} does not have an admin_integration module")
            return False
    
    except Exception as e:
        logger.error(f"Error registering {module_name} with Admin: {str(e)}")
        return False


def register_with_service_registry(module_name: str) -> bool:
    """
    Register a module with the service registry.
    
    Args:
        module_name: Name of the module to register
        
    Returns:
        True if registration was successful, False otherwise
    """
    try:
        # Try to import module interface
        module_interface_path = f"{module_name}.module_interface"
        
        try:
            module_interface = importlib.import_module(module_interface_path)
            
            # Find a class that implements ModuleInterface
            module_class = None
            for attr_name in dir(module_interface):
                attr = getattr(module_interface, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, ModuleInterface) and 
                    attr is not ModuleInterface):
                    module_class = attr
                    break
            
            if module_class:
                # Instantiate the module class
                module_instance = module_class()
                
                # Activate the module
                if module_instance.activate():
                    logger.info(f"Successfully activated {module_name}")
                    return True
                else:
                    logger.warning(f"Failed to activate {module_name}")
                    return False
            else:
                logger.warning(f"No ModuleInterface implementation found in {module_name}")
                return False
                
        except ImportError as e:
            logger.warning(f"Module {module_name} does not have a module_interface implementation: {e}")
            return False
        except Exception as e:
            logger.error(f"Error instantiating module interface for {module_name}: {e}")
            return False
    
    except Exception as e:
        logger.error(f"Error registering {module_name} with service registry: {str(e)}")
        return False


def register_all_modules(admin_url: str = None, api_key: str = None) -> Dict[str, bool]:
    """
    Register all modules with the Admin dashboard.
    
    Args:
        admin_url: URL of the Admin module API
        api_key: API key for authentication
        
    Returns:
        Dictionary of module names to registration success
    """
    results = {}
    
    for module_name in MODULES:
        logger.info(f"Registering module: {module_name}")
        success = register_module(module_name, admin_url, api_key)
        results[module_name] = success
        
        # Add a small delay between registrations to avoid overwhelming the Admin module
        time.sleep(1)
    
    return results


def check_module_health() -> Dict[str, Dict[str, Any]]:
    """
    Check health of all registered modules
    
    Returns:
        Dictionary mapping module names to health status
    """
    health_data = {}
    
    try:
        # Get all registered modules from service registry
        registry = ServiceRegistry.get_instance()
        services = registry.list_all_services()
        
        # Group by module
        modules = {}
        for service_name, info in services.items():
            module_name = info.get("module")
            if module_name:
                if module_name not in modules:
                    modules[module_name] = []
                modules[module_name].append(service_name)
        
        # Check health for each module
        for module_name, service_list in modules.items():
            try:
                # Try to find a health check service for this module
                health_service = registry.get_service(f"{module_name}.health.check")
                
                if health_service:
                    # Call the health check service
                    health_data[module_name] = health_service()
                else:
                    # Try to find a module info service as fallback
                    info_service = registry.get_service(f"{module_name}.info")
                    if info_service:
                        module_info = info_service()
                        health_data[module_name] = {
                            "status": module_info.get("status", "unknown"),
                            "version": module_info.get("version", "unknown"),
                            "services": len(service_list),
                            "message": "Health check service not available, using module info"
                        }
                    else:
                        # No health check service, just report that it's registered
                        health_data[module_name] = {
                            "status": "unknown",
                            "services": len(service_list),
                            "message": "No health check service available"
                        }
            except Exception as e:
                logger.error(f"Error checking health for module {module_name}: {str(e)}")
                health_data[module_name] = {
                    "status": "error",
                    "error": str(e),
                    "services": len(service_list)
                }
    except Exception as e:
        logger.error(f"Error getting service registry: {str(e)}")
        health_data["system"] = {
            "status": "error",
            "error": str(e),
            "message": "Failed to access service registry"
        }
    
    return health_data


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Register CBS modules with Admin dashboard and service registry')
    parser.add_argument('--admin-url', help='URL of the Admin module API')
    parser.add_argument('--api-key', help='API key for authentication')
    parser.add_argument('--module', help='Specific module to register (if not provided, all modules will be registered)')
    parser.add_argument('--service-registry-only', action='store_true', help='Only register with the service registry')
    parser.add_argument('--check-health', action='store_true', help='Check health of registered modules')
    parser.add_argument('--list', action='store_true', help='List available modules')
    parser.add_argument('--verbose', '-v', action='count', default=0, help='Increase verbosity')
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    if args.verbose > 1:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose > 0:
        logging.getLogger().setLevel(logging.INFO)
    
    # List available modules
    if args.list:
        logger.info("Available modules:")
        for module_name in MODULES:
            logger.info(f"  - {module_name}")
        sys.exit(0)
    
    # If only checking health
    if args.check_health:
        health_data = check_module_health()
        
        logger.info("Module health status:")
        all_healthy = True
        for module_name, status in health_data.items():
            status_str = status.get('status', 'unknown')
            services_count = status.get('services', '?')
            version = status.get('version', 'unknown')
            
            if status_str == 'healthy':
                logger.info(f"  ✓ {module_name} (v{version}): {status_str} with {services_count} services")
            elif status_str == 'degraded':
                logger.warning(f"  ⚠ {module_name} (v{version}): {status_str} with {services_count} services")
                all_healthy = False
            else:
                logger.error(f"  ✗ {module_name} (v{version}): {status_str} with {services_count} services")
                all_healthy = False
                
                # Print error details if available
                if 'error' in status:
                    logger.error(f"    Error: {status['error']}")
                if 'message' in status:
                    logger.error(f"    Message: {status['message']}")
        
        # Return appropriate exit code
        sys.exit(0 if all_healthy else 1)
    
    # If registering a specific module
    if args.module:
        if args.module in MODULES:
            logger.info(f"Registering module {args.module}...")
            
            if args.service_registry_only:
                success = register_with_service_registry(args.module)
                logger.info(f"Service registry registration {'successful' if success else 'failed'}")
            else:
                success = register_module(args.module, args.admin_url, args.api_key)
                logger.info(f"Module registration {'successful' if success else 'failed'}")
                
            # Check health if registration was successful
            if success:
                logger.info(f"Checking health for {args.module}...")
                health_data = check_module_health()
                if args.module in health_data:
                    logger.info(f"Health status: {health_data[args.module].get('status', 'unknown')}")
            
            sys.exit(0 if success else 1)
        else:
            logger.error(f"Unknown module: {args.module}")
            logger.info(f"Available modules: {', '.join(MODULES)}")
            sys.exit(1)
    
    # If registering all modules
    else:
        logger.info("Registering all modules...")
        results = register_all_modules(args.admin_url, args.api_key)
        
        # Print registration results
        logger.info("Registration results:")
        for module_name, success in results.items():
            if success:
                logger.info(f"  ✓ {module_name}: Registered successfully")
            else:
                logger.error(f"  ✗ {module_name}: Registration failed")
        
        # Check health status of modules if requested
        if args.check_health:
            logger.info("Checking module health...")
            health_data = check_module_health()
            
            logger.info("Module health status:")
            for module_name, status in health_data.items():
                status_str = status.get('status', 'unknown')
                if status_str == 'healthy':
                    logger.info(f"  ✓ {module_name}: {status_str}")
                elif status_str == 'degraded':
                    logger.warning(f"  ⚠ {module_name}: {status_str}")
                else:
                    logger.error(f"  ✗ {module_name}: {status_str}")
        
        # Exit with non-zero status if any registration failed
        if not all(results.values()):
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1)
