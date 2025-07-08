"""
Partner File Exchange Models - Core Banking System
"""
from .file_models import PartnerFileEntry, PartnerFile

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
