"""
Partner File Exchange Config - Core Banking System
"""
from .file_config import PartnerFileConfig, partner_file_config

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
