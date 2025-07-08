"""
Import System Package

This module provides functions for managing imports in the CBS_PYTHON project.
It helps to ensure that all project modules are accessible regardless of where
the calling module is located.

Features:
- fix_path(): Add the project root to sys.path
- import_module(): Import a module dynamically
- Environment constants: Development, Test, Production
- Environment detection functions: is_production(), is_development(), etc.

Usage:
------
At the top of your Python file, add:

    from utils.lib.packages import fix_path, import_module
    fix_path()  # Ensures the project root is in sys.path

This ensures all project modules are accessible regardless of where the calling module is located.
"""

import sys
import os
import importlib
from pathlib import Path
from enum import Enum

# Environment constants
class Environment:
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"

def fix_path():
    """
    Add the project root to sys.path to ensure all modules are importable.
    Returns the project root path.
    """
    # Get the caller's file and directory
    caller_frame = sys._getframe(1)
    if caller_frame.f_code.co_filename == '<stdin>':  # Called from interactive session
        current_dir = Path.cwd()
    else:
        current_dir = Path(caller_frame.f_code.co_filename).resolve().parent

    # Find the project root
    project_root = find_project_root(current_dir)
    
    # Add to path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    return project_root

def find_project_root(start_dir=None):
    """Find the project root directory based on marker files."""
    if start_dir is None:
        start_dir = Path(sys._getframe(1).f_code.co_filename).resolve().parent
        
    current_dir = Path(start_dir).resolve()
    
    # Go up to find project root (max 10 levels up)
    for _ in range(10):
        # Check if this could be the project root
        if any((current_dir / marker).exists() for marker in ["main.py", "pyproject.toml", "README.md"]):
            return current_dir
        
        # Move up one directory
        parent = current_dir.parent
        if parent == current_dir:  # Reached filesystem root
            break
        current_dir = parent
    
    # Fallback: return 2 levels up from the start directory
    return Path(start_dir).parent.parent

def import_module(module_name, package=None):
    """
    Import a module dynamically.
    Wrapper around importlib.import_module that provides better error messaging.
    """
    try:
        return importlib.import_module(module_name, package)
    except ImportError as e:
        # Try to provide helpful error message
        original_error = str(e)
        if "No module named" in original_error:
            missing_module = original_error.split("'")[1]
            raise ImportError(
                f"Could not import {missing_module}. Make sure it's installed "
                f"or use fix_path() first to ensure the project root is in sys.path."
            ) from e
        raise

def get_environment():
    """Get the current environment."""
    env = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    return env

def is_production():
    """Check if the current environment is production."""
    return get_environment() == Environment.PRODUCTION

def is_development():
    """Check if the current environment is development."""
    return get_environment() == Environment.DEVELOPMENT

def is_test():
    """Check if the current environment is test."""
    return get_environment() == Environment.TEST

def is_debug_enabled():
    """Check if debug mode is enabled."""
    debug_env = os.environ.get("CBS_DEBUG", "False").lower()
    return debug_env in ("true", "1", "yes")

def get_database_connection():
    """
    Get a connection to the database appropriate for the current environment.
    This is a convenience function that imports and calls the database connection function.
    """
    try:
        # Try to import from the new structure
        from database.python.connection import get_connection
    except ImportError:
        try:
            # Try to import from the old structure
            from app.database.connection import get_connection
        except ImportError:
            # Fallback implementation
            def get_connection():
                print("Warning: Using dummy database connection. Install required dependencies.")
                return None
    
    return get_connection()

# Run setup_imports if this module is executed directly
if __name__ == "__main__":
    root = fix_path()
    print(f"Project root set to: {root}")
    print(f"sys.path: {sys.path}")
    print(f"Environment: {get_environment()}")
    print(f"Debug enabled: {is_debug_enabled()}")
