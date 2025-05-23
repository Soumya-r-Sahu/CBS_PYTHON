"""
Credential Value Object

This module defines the Credential value object which
manages sensitive user authentication information.
"""

from dataclasses import dataclass, field
import re
import os
import base64
from datetime import datetime
from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# Import from centralized security utilities
from ....common.security_utils import PasswordUtils


@dataclass
class Credential:
    """
    Value object representing user credentials
    
    This encapsulates password hashing and verification logic
    with immutable value semantics.
    """
    password_hash: str
    salt: bytes
    last_changed: Optional[str] = None
    expire_days: int = 90
    
    def verify_password(self, password: str) -> bool:
        """
        Verify if a password matches the stored hash
        
        Args:
            password: Password to verify
            
        Returns:
            True if password is correct, False otherwise
        """
        return PasswordUtils.verify_password(password, self.password_hash, self.salt)
    
    def update_password(self, new_password: str) -> None:
        """
        Update the password hash
        
        Args:
            new_password: New password
            
        Raises:
            ValueError: If password doesn't meet complexity requirements
        """
        # Validate password strength
        if not PasswordUtils.validate_password_strength(new_password):
            raise ValueError(
                "Password must be at least 12 characters and include uppercase, "
                "lowercase, digit, and special character"
            )
        
        # Generate new hash and salt
        password_hash, salt = PasswordUtils.generate_password_hash(new_password)
        
        # Update object (despite being mostly immutable, we allow this operation)
        object.__setattr__(self, 'password_hash', password_hash)
        object.__setattr__(self, 'salt', salt)
        object.__setattr__(self, 'last_changed', datetime.now().isoformat())
    
    @staticmethod
    def create(password: str) -> 'Credential':
        """
        Create a new Credential from a plain password
        
        Args:
            password: Plain text password
            
        Returns:
            New Credential object
            
        Raises:
            ValueError: If password doesn't meet complexity requirements
        """
        # Validate password strength
        if not PasswordUtils.validate_password_strength(password):
            raise ValueError(
                "Password must be at least 12 characters and include uppercase, "
                "lowercase, digit, and special character"
            )
        
        # Generate hash and salt
        password_hash, salt = PasswordUtils.generate_password_hash(password)
          # Create credential with current timestamp
        return Credential(
            password_hash=password_hash,
            salt=salt,
            last_changed=datetime.now().isoformat()
        )
