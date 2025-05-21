"""
Service Registration Test Script

This script tests service registration for CRM and HR_ERP modules.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import modules
try:
    from crm.module_interface import CrmModule
    from hr_erp.module_interface import HrErpModule
    from utils.lib.service_registry import ServiceRegistry
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

def test_module_registration(module_name, module_class):
    """Test registration for a specific module"""
    logger.info(f"Testing {module_name} module...")
    
    try:
        # Initialize module
        module = module_class()
        logger.info(f"Module initialized: {module.name} v{module.version}")
        
        # Register services
        result = module.register_services()
        logger.info(f"Services registered: {len(module.service_registrations)}")
        
        # Get services from registry
        registry = ServiceRegistry()
        services = registry.list_services()
        services_for_module = [s for s in services if s.get('module') == module.name]
        logger.info(f"Services found in registry: {len(services_for_module)}")
        
        return {
            "name": module.name,
            "version": module.version,
            "services_registered": len(module.service_registrations),
            "services_in_registry": len(services_for_module),
            "success": result
        }
    except Exception as e:
        logger.error(f"Error testing {module_name} module: {e}")
        return {
            "name": module_name,
            "success": False,
            "error": str(e)
        }

def main():
    """Main function"""
    logger.info("Starting service registration test...")
    
    results = []
    
    # Test CRM module
    crm_result = test_module_registration("CRM", CrmModule)
    results.append(crm_result)
    
    # Test HR_ERP module
    hr_erp_result = test_module_registration("HR_ERP", HrErpModule)
    results.append(hr_erp_result)
    
    # Print results
    logger.info("-" * 50)
    logger.info("Test Results:")
    for result in results:
        if result.get("success"):
            logger.info(f"✓ {result['name']} v{result['version']}: {result['services_registered']} services registered")
        else:
            logger.info(f"✗ {result['name']}: Failed - {result.get('error', 'Unknown error')}")
    logger.info("-" * 50)

if __name__ == "__main__":
    main()
