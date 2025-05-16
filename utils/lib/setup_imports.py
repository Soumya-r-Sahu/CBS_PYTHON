"""
Setup Imports Helper

This module provides a simple way to set up imports for modules in the CBS_PYTHON project.
It should be the first thing imported in any module that needs to access other project modules.

Usage:
------
At the top of your Python file, add:

    from app.lib.setup_imports import setup_imports
    setup_imports()

If that fails (because app.lib isn't in sys.path yet), it includes a fallback:

    import os
    import sys
    from pathlib import Path
    
    # Try to use the centralized import system
    try:
        # First, try to add app/lib to path temporarily
        lib_path = Path(__file__).resolve().parent
        for _ in range(10):  # Look up to 10 levels
            if (lib_path / "app" / "lib").exists():
                sys.path.insert(0, str(lib_path / "app" / "lib"))
                break
            parent = lib_path.parent
            if parent == lib_path:  # Reached filesystem root
                break
            lib_path = parent
            
        from setup_imports import setup_imports
        setup_imports()
    except ImportError:
        # Fallback: Add parent directory to path
        project_root = Path(__file__).resolve().parent
        while not any((project_root / marker).exists() 
                    for marker in ["main.py", "pyproject.toml", "README.md"]):
            project_root = project_root.parent
            if project_root == project_root.parent:  # Reached filesystem root
                project_root = Path(__file__).resolve().parent.parent  # Fallback
                break
                
        sys.path.insert(0, str(project_root))
        print(f"Warning: Using direct path modification. Path: {project_root}")

This ensures all project modules are accessible regardless of where the calling module is located.
"""

import sys
import os
from pathlib import Path

def setup_imports():
    """
    Set up the import system for the current module.
    This ensures that all project modules are accessible.
    """
    try:
        # If import_manager is already in sys.path, use it directly
        from utils.lib.packages import fix_path
        return fix_path()
    except ImportError:
        # Try to find and add the import_manager module
        current_file = Path(sys._getframe(1).f_code.co_filename).resolve()
        current_dir = current_file.parent
        
        # Try to find app/lib up to 10 levels up
        lib_path = None
        search_dir = current_dir
        for _ in range(10):
            # Check if this could be the project root (has app/lib)
            if (search_dir / "app" / "lib").is_dir():
                lib_path = search_dir / "app" / "lib"
                break
                
            # Look for app/lib
            if "app" in (d.name for d in search_dir.iterdir() if d.is_dir()):
                app_dir = search_dir / "app"
                if "lib" in (d.name for d in app_dir.iterdir() if d.is_dir()):
                    lib_path = app_dir / "lib"
                    break
            
            # Move up one directory
            parent = search_dir.parent
            if parent == search_dir:  # Reached filesystem root
                break
            search_dir = parent
        
        if lib_path and lib_path not in [Path(p) for p in sys.path]:
            sys.path.insert(0, str(lib_path))
            try:
                from utils.lib.packages import fix_path
                return fix_path()
            except ImportError:
                pass
        
        # Fallback: Find project root and add to path
        project_root = find_project_root(current_dir)
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

# Run setup_imports if this module is executed directly
if __name__ == "__main__":
    root = setup_imports()
    print(f"Project root set to: {root}")
    print(f"sys.path: {sys.path}")
