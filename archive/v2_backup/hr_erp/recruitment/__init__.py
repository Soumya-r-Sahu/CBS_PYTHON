"""
Recruitment Package

This package contains modules for managing job openings, applications, interviews, and hiring processes.
"""

from .recruitment_manager import RecruitmentManager, get_recruitment_manager


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
__all__ = ['RecruitmentManager', 'get_recruitment_manager']
