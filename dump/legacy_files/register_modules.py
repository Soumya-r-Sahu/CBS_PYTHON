"""
CBS Module Registration

This script registers all CBS modules with the Admin dashboard.
It collects module information, API endpoints, feature flags, 
and configurations from each module and sends them to the Admin module.
"""
import os
import sys
import logging
import importlib
import argparse
from typing import List, Dict, Any
import time

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
    # Add new modules here in the appropriate order
]

def register_module(module_name: str, admin_url: str = None, api_key: str = None) -> bool:
    """
    Register a module with the Admin dashboard.
    
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
        
        # Import the module's admin_integration module
        module_path = f"{module_name}.admin_integration"
        
        try:
            module = importlib.import_module(module_path)
        except ImportError:
            logger.warning(f"Module {module_name} does not have an admin_integration module")
            return False
        
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
    
    except Exception as e:
        logger.error(f"Error registering {module_name}: {str(e)}")
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


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Register CBS modules with Admin dashboard')
    parser.add_argument('--admin-url', help='URL of the Admin module API')
    parser.add_argument('--api-key', help='API key for authentication')
    parser.add_argument('--module', help='Specific module to register (if not provided, all modules will be registered)')
    args = parser.parse_args()
    
    if args.module:
        if args.module in MODULES:
            success = register_module(args.module, args.admin_url, args.api_key)
            sys.exit(0 if success else 1)
        else:
            logger.error(f"Unknown module: {args.module}")
            logger.info(f"Available modules: {', '.join(MODULES)}")
            sys.exit(1)
    else:
        results = register_all_modules(args.admin_url, args.api_key)
        
        # Print registration results
        logger.info("Registration results:")
        for module_name, success in results.items():
            logger.info(f"  {module_name}: {'Success' if success else 'Failed'}")
        
        # Exit with non-zero status if any registration failed
        if not all(results.values()):
            sys.exit(1)


if __name__ == "__main__":
    main()
