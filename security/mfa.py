"""
Multi-Factor Authentication Module

This module provides MFA functionality for the security system.
It's a wrapper around the actual implementation in the authentication package.
"""

from security.authentication.mfa import (
    setup_mfa, verify_mfa, disable_mfa, regenerate_backup_codes
)

# Re-export all functions
__all__ = [
    'setup_mfa', 
    'verify_mfa', 
    'disable_mfa', 
    'regenerate_backup_codes'
]
