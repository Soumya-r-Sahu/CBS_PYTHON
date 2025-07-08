"""
Core Banking System Import Manager (LEGACY VERSION)

This module provides backward compatibility with the old import system.
It forwards all functionality to the new import system in utils/lib/packages.py.

This is a legacy module kept for backward compatibility only.
New code should use utils/lib/packages instead.
"""

import sys
import os
import importlib
import warnings
from pathlib import Path

# Forward all functionality to the packages module
try:
    from utils.lib.packages import fix_path, import_module, find_project_root
    from utils.lib.packages import get_environment, is_production, is_development, is_test, is_debug_enabled
    from utils.lib.packages import Environment, get_database_connection
    
    # Issue a deprecation warning
    warnings.warn(
        "The app.lib.import_manager module is deprecated. "
        "Please use utils.lib.packages instead.",
        DeprecationWarning,
        stacklevel=2
    )
except ImportError:
    # If packages.py isn't available, provide fallback implementations
    print("Warning: Could not import utils.lib.packages. Using fallback implementations.")
    
    def fix_path():
        """Add the project root to sys.path."""
        project_root = find_project_root()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        return project_root
    
    def find_project_root(start_dir=None):
        """Find the project root directory."""
        if start_dir is None:
            import inspect
            frame = inspect.currentframe().f_back
            start_dir = Path(frame.f_code.co_filename).resolve().parent
        
        current_dir = Path(start_dir).resolve()
        for _ in range(10):  # Look up to 10 levels
            if any((current_dir / marker).exists() for marker in ["main.py", "pyproject.toml", "README.md"]):
                return current_dir
            parent = current_dir.parent
            if parent == current_dir:  # Reached filesystem root
                break
            current_dir = parent
        return Path(start_dir).parent.parent  # Fallback
    
    def import_module(name, package=None):
        """Import a module."""
        return importlib.import_module(name, package)
    
    class Environment:
        """Environment constants."""
        DEVELOPMENT = "development"
        TEST = "test"
        PRODUCTION = "production"
    
    def get_environment():
        """Get the current environment."""
        return os.environ.get("CBS_ENVIRONMENT", Environment.DEVELOPMENT)
    
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
        return os.environ.get("CBS_DEBUG", "").lower() in ("true", "1", "yes")
    
    def get_database_connection():
        """Get a database connection."""
        print("Warning: Database connection not available in fallback mode")
        return None

# For backward compatibility
def fix_path():
    """Add the project root to sys.path."""
    from utils.lib.packages import fix_path as utils_fix_path
    return utils_fix_path()

# This is the function exposed by the original import_manager module
def setup_imports():
    """Set up the import system."""
    warnings.warn(
        "setup_imports() from import_manager is deprecated. "
        "Please use fix_path() from utils.lib.packages instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return fix_path()
