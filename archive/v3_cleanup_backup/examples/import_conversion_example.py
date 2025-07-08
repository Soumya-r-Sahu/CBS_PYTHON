#!/usr/bin/env python
"""
Example Import Conversion Script

This script shows how to convert existing direct sys.path manipulation
to use the centralized import manager.
"""

# =================================================================
# BEFORE: Using direct sys.path modification
# =================================================================

# Bad practice - direct sys.path modification
import sys
import os
from pathlib import Path

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, project_root)

# Import modules directly
import database.python.connection
from app.config import environment
from utils.logging import setup_logging

# Check the environment
if environment.is_production():
    print("Running in production mode")
else:
    print("Not in production")

# =================================================================
# AFTER: Using the centralized import manager
# =================================================================

# Good practice - use the centralized import manager
try:
    # Import the import manager
    from utils.lib.packages import (
        # Core functions
        import_module, fix_path,
        
        # Environment functions
        is_production, is_development, is_test,
        
        # Database connection
        get_database_connection
    )
    
    # No need to modify sys.path manually
    # The fix_path function has already handled this
    
    # Import modules using the import manager
    db_connection_module = import_module('database.python.connection')
    
    # Use the imported modules
    DB = db_connection_module.DatabaseConnection()
    
    # Use the environment functions directly
    if is_production():
        print("Running in production mode")
    else:
        print("Not in production")
    
    # Use the database connection helper
    DatabaseConnection = get_database_connection()
    with DatabaseConnection().transaction() as (conn, cursor):
        # Use the connection and cursor
        pass

# Fallback for when the import manager is not available
except ImportError:
    print("Import manager not available, using direct sys.path modification")
    
    # Add project root to sys.path manually
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Import modules directly
    import database.python.connection
    from app.config import environment
    
    # Check the environment
    if environment.is_production():
        print("Running in production mode")
    else:
        print("Not in production")
