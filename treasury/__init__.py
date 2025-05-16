"""
Treasury Management Module for Core Banking System.

This module manages all treasury operations including bonds, derivatives,
foreign exchange, and liquidity management functions for the bank.
"""

from pathlib import Path
import sys
import os

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


# Version info
__version__ = '0.1.0'