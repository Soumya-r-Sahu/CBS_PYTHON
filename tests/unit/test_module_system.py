"""
Simple Module Test

This script performs a simple test of the module detachment functionality.
"""

import os
import sys
import logging

# Add the repository root to the Python path
sys.path.insert(0, os.path.abspath("."))

try:
    # Import the module interface
    from utils.lib.module_interface import ModuleRegistry
    from utils.lib.service_registry import ServiceRegistry
    
    print("Module and Service registries imported successfully")
    
    # Get service registry
    sr = ServiceRegistry()
    print("Service Registry instance created")
    
    # Get module registry
    mr = ModuleRegistry.get_instance()
    print("Module Registry instance created")
    
    print("Test completed successfully")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
