"""
Setup Imports Helper (LEGACY VERSION)

This module provides backward compatibility with the old import system. 
It forwards calls to the new import system in utils/lib/packages.py.

Usage:
------
At the top of your Python file, add:

    from app.lib.setup_imports import setup_imports
    setup_imports()

However, it's recommended to update your code to use the new import system:

    from utils.lib.packages import fix_path
    fix_path()

This is a legacy module that forwards to the new import system in utils/lib/packages.py.
"""

import sys
import os
import warnings
from pathlib import Path

def setup_imports():
    """
    Set up the import system for the current module.
    This ensures that all project modules are accessible.
    Forward to the new utils.lib.packages.fix_path function.
    """
    try:
        # Try to use the new import system
        from utils.lib.packages import fix_path
        warnings.warn(
            "Using app.lib.setup_imports is deprecated. "
            "Please update your code to use utils.lib.packages instead.", 
            DeprecationWarning, 
            stacklevel=2
        )
        return fix_path()
    except ImportError:
        # If the new system is not available, log an error but don't modify sys.path directly
        print("ERROR: utils.lib.packages module not available.")
        print("Please install/update your project correctly to use the new import system.")
        print("For more information, see documentation/migration_guides/import_system_migration.md")
        return None

def find_project_root():
    """
    Find the root directory of the project.
    DEPRECATED: This function is kept for backward compatibility but should not be used directly.
    """
    warnings.warn(
        "Using find_project_root() is deprecated. "
        "Please update your code to use utils.lib.packages.get_project_root() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        from utils.lib.packages import get_project_root
        return get_project_root()
    except ImportError:
        print("ERROR: utils.lib.packages module not available.")
        print("Please install/update your project correctly to use the new import system.")
        print("For more information, see documentation/migration_guides/import_system_migration.md")
        return Path(__file__).resolve().parent.parent.parent

class HyphenatedDirectoryFinder:
    """
    DEPRECATED: This class is kept for backward compatibility but should not be used directly.
    Use utils.lib.packages.import_module() instead.
    """
    def __init__(self, base_dir=None):
        warnings.warn(
            "Using HyphenatedDirectoryFinder is deprecated. "
            "Please update your code to use utils.lib.packages.import_module() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.base_dir = base_dir or find_project_root()
    
    def find_module(self, fullname, path=None):
        warnings.warn(
            "Using HyphenatedDirectoryFinder.find_module is deprecated. "
            "Please update your code to use utils.lib.packages.import_module() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return None
