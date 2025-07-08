#!/usr/bin/env python
"""
Environment Information Script

This script displays information about the current environment configuration.
It helps developers and administrators understand what environment they're working in.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path if needed
# Commented out direct sys.path modification
# sys.path.insert(0, str(Path(__file__)


# Use centralized import manager if available
try:
    # Import from utils/lib
    from utils.lib.packages import fix_path
    fix_path()  # Ensures project root is in sys.path
except ImportError:
    # Fallback: add parent directory to path directly
    pass

try:
    from app.config.environment import (
        get_environment_name, get_environment_config, 
        is_production, is_development, is_test, is_debug_enabled
    )
    
    print("\n=== Core Banking System: Environment Information ===\n")
    print(f"Environment: {get_environment_name().upper()}")
    print(f"Debug Mode: {'Enabled' if is_debug_enabled() else 'Disabled'}")
    
    env_specific = "PRODUCTION" if is_production() else "TEST" if is_test() else "DEVELOPMENT"
    print(f"Environment Type: {env_specific}")
    
    # Show key environment variables
    print("\nKey Environment Variables:")
    relevant_vars = [var for var in os.environ if var.startswith("CBS_")]
    for var in sorted(relevant_vars):
        # Hide sensitive values
        if any(sensitive in var.lower() for sensitive in ["password", "secret", "key"]):
            print(f"  {var}: ***HIDDEN***")
        else:
            print(f"  {var}: {os.environ[var]}")
    
    # Show full configuration
    print("\nFull Environment Configuration:")
    for key, value in get_environment_config().items():
        print(f"  {key}: {value}")
    
    print("\n=== End of Environment Information ===\n")
    
except ImportError as e:
    print(f"\nError: Could not import environment module: {e}")
    print("Using fallback method to display environment information.\n")
    
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    debug_mode = os.environ.get("CBS_DEBUG", "true").lower() in ("true", "1", "yes")
    
    print(f"Environment: {env_str.upper()}")
    print(f"Debug Mode: {'Enabled' if debug_mode else 'Disabled'}")
    
    # Show key environment variables
    print("\nKey Environment Variables:")
    relevant_vars = [var for var in os.environ if var.startswith("CBS_")]
    for var in sorted(relevant_vars):
        if any(sensitive in var.lower() for sensitive in ["password", "secret", "key"]):
            print(f"  {var}: ***HIDDEN***")
        else:
            print(f"  {var}: {os.environ[var]}")

if __name__ == "__main__":
    # Script already ran when imported
    pass
