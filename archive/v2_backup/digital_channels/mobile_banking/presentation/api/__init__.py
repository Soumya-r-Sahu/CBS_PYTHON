# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

"""
API presentation layer for Mobile Banking module.
"""

from .mobile_controller import mobile_api, register_blueprint

__all__ = ['mobile_api', 'register_blueprint']
