"""
Foreign Exchange (Forex) management package for treasury operations.

This package provides functionality for managing currency positions, exchange rates,
foreign exchange trading operations, and currency risk management.
"""

from pathlib import Path
import os
import sys

# Add current directory to path to ensure local imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    # Use centralized import manager
    try:
        from utils.lib.packages import fix_path, import_module
        fix_path()  # Ensures the project root is in sys.path
    except ImportError:
        # Fallback for when the import manager is not available
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed
