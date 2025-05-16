"""
Partner File Exchange Controllers - Core Banking System
"""
from .file_controller import PartnerFileController

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
