"""
Password Manager Module

This module provides password management functionality for the security system.
It's a wrapper around the actual implementation in the authentication package.
"""

from security.authentication.password_manager import (
    hash_password, verify_password, validate_password_policy,
    generate_secure_password, check_password_expiration
)

# Re-export all functions
__all__ = [
    'hash_password', 
    'verify_password', 
    'validate_password_policy',
    'generate_secure_password', 
    'check_password_expiration'
]
