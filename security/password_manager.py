"""
Password Management for Core Banking System

This module provides secure password management functionality,
including password hashing, validation, and policy enforcement.
"""

import re
import os
import time
import hashlib
import logging
import secrets
import string
from typing import Tuple, Dict, Any, Optional

# Configure logger
logger = logging.getLogger(__name__)

# Password policy constants
PASSWORD_MIN_LENGTH = 10
PASSWORD_MIN_UPPERCASE = 1
PASSWORD_MIN_LOWERCASE = 1
PASSWORD_MIN_DIGITS = 1
PASSWORD_MIN_SPECIAL = 1
PASSWORD_SPECIAL_CHARS = "!@#$%^&*()-_=+[]{}|;:,.<>?/"
PASSWORD_HISTORY_SIZE = 5  # Number of previous passwords to remember
PASSWORD_MAX_AGE_DAYS = 90  # Maximum password age before requiring change


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Securely hash a password using Argon2 or PBKDF2.
    
    Args:
        password (str): The password to hash
        salt (str, optional): Salt to use, if None a new salt is generated
        
    Returns:
        Tuple[str, str]: (hashed_password, salt)
    """
    try:
        # Try to use Argon2 if available (more secure)
        import argon2
        ph = argon2.PasswordHasher()
        if salt is None:
            # Argon2 handles salt internally
            hashed = ph.hash(password)
            # Extract salt for storage (format: $argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>)
            salt_parts = hashed.split('$')
            if len(salt_parts) >= 4:
                salt = salt_parts[4]
        else:
            # Use provided salt with Argon2
            hashed = ph.hash(password + salt)
        
        return hashed, salt
    except ImportError:
        # Fallback to PBKDF2 with SHA-256
        logger.info("Argon2 not available, falling back to PBKDF2")
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use a high iteration count for security
        iterations = 600000
        
        # Hash the password with PBKDF2
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        
        # Convert to hex string
        hashed = f"pbkdf2:sha256:{iterations}${salt}${key.hex()}"
        
        return hashed, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """
    Verify a password against its stored hash.
    
    Args:
        password (str): The password to verify
        stored_hash (str): The stored hash
        salt (str): The salt used in hashing
        
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        # Check if hash is in Argon2 format
        if stored_hash.startswith("$argon2"):
            import argon2
            ph = argon2.PasswordHasher()
            try:
                ph.verify(stored_hash, password)
                return True
            except (argon2.exceptions.VerifyMismatchError, ValueError):
                return False
        
        # Check if hash is in PBKDF2 format
        elif stored_hash.startswith("pbkdf2"):
            parts = stored_hash.split('$')
            if len(parts) != 3:
                return False
            
            algo_info, stored_salt, stored_key = parts
            algo_parts = algo_info.split(':')
            if len(algo_parts) != 3:
                return False
            
            _, hash_name, iterations = algo_parts
            iterations = int(iterations)
            
            # Compute hash with same parameters
            key = hashlib.pbkdf2_hmac(
                hash_name,
                password.encode('utf-8'),
                stored_salt.encode('utf-8'),
                iterations
            )
            
            return key.hex() == stored_key
        
        # Unknown format
        else:
            logger.error(f"Unknown password hash format: {stored_hash[:10]}...")
            return False
    
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False


def validate_password_policy(password: str) -> Dict[str, Any]:
    """
    Validate password against the security policy.
    
    Args:
        password (str): The password to validate
        
    Returns:
        Dict[str, Any]: Validation result with 'valid' flag and 'errors'
    """
    errors = []
    
    # Check length
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
    
    # Check uppercase
    if sum(1 for c in password if c.isupper()) < PASSWORD_MIN_UPPERCASE:
        errors.append(f"Password must contain at least {PASSWORD_MIN_UPPERCASE} uppercase letter(s)")
    
    # Check lowercase
    if sum(1 for c in password if c.islower()) < PASSWORD_MIN_LOWERCASE:
        errors.append(f"Password must contain at least {PASSWORD_MIN_LOWERCASE} lowercase letter(s)")
    
    # Check digits
    if sum(1 for c in password if c.isdigit()) < PASSWORD_MIN_DIGITS:
        errors.append(f"Password must contain at least {PASSWORD_MIN_DIGITS} digit(s)")
    
    # Check special characters
    special_count = sum(1 for c in password if c in PASSWORD_SPECIAL_CHARS)
    if special_count < PASSWORD_MIN_SPECIAL:
        errors.append(f"Password must contain at least {PASSWORD_MIN_SPECIAL} special character(s)")
    
    # Check common patterns
    common_patterns = [
        "123456", "password", "qwerty", "admin", "welcome",
        "abc123", "letmein", "monkey", "1234", "12345"
    ]
    
    for pattern in common_patterns:
        if pattern.lower() in password.lower():
            errors.append(f"Password contains a common pattern ({pattern})")
            break
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a secure random password that meets policy requirements.
    
    Args:
        length (int): The length of the password to generate
        
    Returns:
        str: A secure random password
    """
    if length < PASSWORD_MIN_LENGTH:
        length = PASSWORD_MIN_LENGTH
    
    # Character sets
    uppercase_letters = string.ascii_uppercase
    lowercase_letters = string.ascii_lowercase
    digits = string.digits
    special_chars = PASSWORD_SPECIAL_CHARS
    
    # Ensure at least one character from each set
    password = [
        secrets.choice(uppercase_letters),
        secrets.choice(lowercase_letters),
        secrets.choice(digits),
        secrets.choice(special_chars)
    ]
    
    # Fill the rest with random characters from all sets
    all_chars = uppercase_letters + lowercase_letters + digits + special_chars
    password.extend(secrets.choice(all_chars) for _ in range(length - len(password)))
    
    # Shuffle the password characters
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def check_password_expiration(last_changed_timestamp: float) -> Dict[str, Any]:
    """
    Check if a password has expired based on age policy.
    
    Args:
        last_changed_timestamp (float): Timestamp when password was last changed
        
    Returns:
        Dict[str, Any]: Expiration status with 'expired' flag and 'days_left'
    """
    current_time = time.time()
    days_since_change = (current_time - last_changed_timestamp) / (24 * 60 * 60)
    days_left = PASSWORD_MAX_AGE_DAYS - days_since_change
    
    return {
        "expired": days_left <= 0,
        "days_left": max(0, int(days_left)),
        "days_since_change": int(days_since_change)
    }


def is_password_reused(new_password: str, password_history: list) -> bool:
    """
    Check if a password has been used before.
    
    Args:
        new_password (str): The new password to check
        password_history (list): List of previous password hashes and salts
        
    Returns:
        bool: True if the password was used before, False otherwise
    """
    for old_entry in password_history:
        old_hash = old_entry.get('hash')
        old_salt = old_entry.get('salt')
        
        if verify_password(new_password, old_hash, old_salt):
            return True
    
    return False


if __name__ == "__main__":
    # Example usage
    test_password = "Secure@Password123"
    
    # Validate against policy
    validation = validate_password_policy(test_password)
    if validation["valid"]:
        print(f"Password meets policy requirements")
    else:
        print(f"Password does not meet policy requirements:")
        for error in validation["errors"]:
            print(f"- {error}")
    
    # Hash the password
    hashed, salt = hash_password(test_password)
    print(f"Hashed password: {hashed}")
    print(f"Salt: {salt}")
    
    # Verify the password
    is_valid = verify_password(test_password, hashed, salt)
    print(f"Password verification: {'Success' if is_valid else 'Failed'}")
    
    # Generate a secure password
    secure_password = generate_secure_password()
    print(f"Generated secure password: {secure_password}")
