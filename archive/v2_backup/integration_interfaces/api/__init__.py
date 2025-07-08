"""
Mobile Banking API for Core Banking System
"""

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

# Import API routes from the local module
from integration_interfaces.api.routes import setup_routes

__all__ = ['setup_routes']
