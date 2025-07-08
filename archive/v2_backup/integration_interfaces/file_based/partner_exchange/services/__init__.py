"""
Partner File Exchange Services - Core Banking System
"""
from .file_service import PartnerFileService, partner_file_service

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
