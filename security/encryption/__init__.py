"""
Core Banking System - Security Encryption Subpackage

This package provides encryption and decryption functionality for the Core Banking System.
"""

from security.common.encryption.encryption import encrypt_text, decrypt_text

# Export the main functions for direct import from the package
__all__ = ["encrypt_text", "decrypt_text"]
