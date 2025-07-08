"""
Admin Module Integration Test

This script tests the end-to-end integration between the Admin module and other modules.
It verifies that modules can register, report health, and receive configuration updates.
"""
import os
import sys
import logging
import time
import json
import argparse
import requests
from typing import Dict, List, Any

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from register_modules import register_all_modules
from integration_interfaces.api.admin_client import AdminIntegrationClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_module_registration(admin_url: str, api_key: str) -> bool:
    """
    Test module registration with the Admin module.
    
    Args:
        admin_url: URL of the Admin module API
        api_key: API key for authentication
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Testing module registration...")
    
    # Register all modules
    results = register_all_modules(admin_url, api_key)
    
    # Check if all modules were registered successfully
    if all(results.values()):
        logger.info("All modules registered successfully")
        return True
    else:
        failed_modules = [name for name, success in results.items() if not success]
        logger.warning(f"Failed to register modules: {', '.join(failed_modules)}")
        return False

def test_module_health_reporting(admin_url: str, api_key: str) -> bool:
    """
    Test health reporting from modules to the Admin module.
    
    Args:
        admin_url: URL of the Admin module API
        api_key: API key for authentication
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Testing module health reporting...")
    
    # Create an admin client
    client = AdminIntegrationClient(
        admin_base_url=admin_url,
        module_id="test_script",
        api_key=api_key
    )
    
    try:
        # Get all modules
        modules = client.get_modules()
        
        # Check if we got modules
        if not modules or "modules" not in modules or not modules["modules"]:
            logger.warning("No modules found in Admin module")
            return False
        
        # Check health status for each module
        all_healthy = True
        for module in modules["modules"]:
            module_id = module.get("id")
            if not module_id:
                continue
            
            # Get health status
            health = client.get_module_health(module_id)
            
            if not health or "status" not in health:
                logger.warning(f"Failed to get health status for module {module_id}")
                all_healthy = False
            else:
                status = health.get("status")
                logger.info(f"Module {module_id} health status: {status}")
                
                if status not in ("healthy", "warning"):
                    logger.warning(f"Module {module_id} is not healthy: {status}")
                    all_healthy = False
        
        return all_healthy
    except Exception as e:
        logger.error(f"Error testing health reporting: {str(e)}")
        return False

def test_configuration_updates(admin_url: str, api_key: str) -> bool:
    """
    Test configuration updates from the Admin module to modules.
    
    Args:
        admin_url: URL of the Admin module API
        api_key: API key for authentication
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Testing configuration updates...")
    
    # Create an admin client
    client = AdminIntegrationClient(
        admin_base_url=admin_url,
        module_id="test_script",
        api_key=api_key
    )
    
    try:
        # Get all modules
        modules = client.get_modules()
        
        # Check if we got modules
        if not modules or "modules" not in modules or not modules["modules"]:
            logger.warning("No modules found in Admin module")
            return False
        
        # Test updating configuration for a module
        test_module = modules["modules"][0]  # Use the first module for testing
        module_id = test_module.get("id")
        
        if not module_id:
            logger.warning("No module ID found for testing")
            return False
        
        # Get current configurations
        configs = client.get_configurations(module_id)
        
        if not configs or "configurations" not in configs or not configs["configurations"]:
            logger.warning(f"No configurations found for module {module_id}")
            return False
        
        # Choose a configuration to update
        config = configs["configurations"][0]
        config_key = config.get("key")
        config_value = config.get("value")
        
        if not config_key:
            logger.warning(f"No configuration key found for module {module_id}")
            return False
        
        # Update the configuration
        new_value = f"test_value_{int(time.time())}" if isinstance(config_value, str) else 42
        
        update_result = client.update_configuration(module_id, config_key, new_value)
        
        if not update_result or "status" not in update_result or update_result["status"] != "success":
            logger.warning(f"Failed to update configuration for module {module_id}")
            return False
        
        logger.info(f"Successfully updated configuration for module {module_id}: {config_key} = {new_value}")
        
        # Wait for the configuration update to propagate
        logger.info("Waiting for configuration update to propagate...")
        time.sleep(5)
        
        # Verify the configuration was updated
        configs = client.get_configurations(module_id)
        
        for config in configs.get("configurations", []):
            if config.get("key") == config_key:
                if config.get("value") == new_value:
                    logger.info(f"Configuration update verified for module {module_id}: {config_key} = {new_value}")
                    return True
                else:
                    logger.warning(f"Configuration update not reflected for module {module_id}: {config_key}")
                    return False
        
        logger.warning(f"Configuration not found after update for module {module_id}: {config_key}")
        return False
    except Exception as e:
        logger.error(f"Error testing configuration updates: {str(e)}")
        return False

def run_integration_tests(admin_url: str, api_key: str) -> Dict[str, bool]:
    """
    Run all integration tests.
    
    Args:
        admin_url: URL of the Admin module API
        api_key: API key for authentication
        
    Returns:
        Dictionary of test names to test results
    """
    results = {}
    
    # Test module registration
    results["module_registration"] = test_module_registration(admin_url, api_key)
    
    # Test module health reporting
    results["health_reporting"] = test_module_health_reporting(admin_url, api_key)
    
    # Test configuration updates
    results["configuration_updates"] = test_configuration_updates(admin_url, api_key)
    
    return results

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test Admin module integration')
    parser.add_argument('--admin-url', type=str, help='URL of the Admin module API')
    parser.add_argument('--api-key', type=str, help='API key for authentication')
    args = parser.parse_args()
    
    # Get admin URL and API key from arguments or environment
    admin_url = args.admin_url or os.environ.get("CBS_ADMIN_BASE_URL", "http://localhost:8000/api/admin")
    api_key = args.api_key or os.environ.get("CBS_ADMIN_API_KEY")
    
    if not api_key:
        logger.error("No API key provided. Please provide an API key with --api-key or set the CBS_ADMIN_API_KEY environment variable.")
        sys.exit(1)
    
    # Run the tests
    results = run_integration_tests(admin_url, api_key)
    
    # Print results
    logger.info("Test results:")
    for test_name, result in results.items():
        logger.info(f"  {test_name}: {'PASS' if result else 'FAIL'}")
    
    # Exit with success if all tests passed, otherwise fail
    if all(results.values()):
        logger.info("All tests passed")
        sys.exit(0)
    else:
        logger.error("Some tests failed")
        sys.exit(1)
