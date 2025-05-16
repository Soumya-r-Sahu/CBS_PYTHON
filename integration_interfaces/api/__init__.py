"""
Mobile Banking API for Core Banking System
"""

from app.api.routes import setup_routes


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
__all__ = ['setup_routes']
