#!/usr/bin/env python
"""
Example of using the centralized import manager.

This file demonstrates how to use the centralized import manager in your code.
"""

# Before using the centralized import manager, you would have to do this:
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Now, you can just do this:
import sys
from pathlib import Path

# Add project root to path to find utils.lib.packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from utils.lib.packages import (
        # Core functions
        import_module, fix_path,
        
        # Environment functions
        is_production, is_development, is_test,
        
        # Database helpers
        get_database_connection
    )
    
    # The path is fixed automatically when importing packages.py
    print("Using the centralized import manager")
    
    # Example: Check environment
    print("\nEnvironment checks:")
    if is_production():
        print("Running in production mode")
    else:
        print("Running in development/test mode")

    # Example: Import a module
    config = import_module("config")
    print(f"\nImported config module: {config.__name__}")

    # Example: Use database connection
    print("\nGetting database connection:")
    DBConnection = get_database_connection()
    db = DBConnection()
    print(f"Database connection class: {db.__class__.__name__}")

except ImportError as e:
    print(f"Error importing the centralized import manager: {e}")

print("\nFinished example!")
