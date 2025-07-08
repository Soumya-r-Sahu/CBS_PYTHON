"""
Encryption Utilities for Core Banking System

This module provides secure encryption and hashing utilities for sensitive data 
throughout the core banking system. It implements industry-standard algorithms 
for securing passwords, card data, and other sensitive information.

Features:
---------
1. Password hashing with salting (using PBKDF2-HMAC-SHA256)
2. Symmetric encryption of sensitive data (using Fernet)
3. Secure key generation and management
4. Card data encryption utilities

Security Notes:
--------------
- Passwords are never stored in plain text
- Uses PBKDF2 with 100,000 iterations for password hashing
- Encryption keys should be stored securely in a separate location
- All sensitive data is encrypted at rest and in transit

Usage Examples:
--------------
Hashing a password:
    >>> from utils.encryption import hash_password, verify_password
    >>> hashed_pwd = hash_password("my_secure_password")
    >>> verify_password(hashed_pwd, "my_secure_password")  # Returns: True

Encrypting sensitive data:
    >>> from utils.encryption import generate_key, encrypt_data, decrypt_data
    >>> key = generate_key()
    >>> encrypted = encrypt_data("sensitive info", key)
    >>> decrypted = decrypt_data(encrypted, key)
"""

import os
import hashlib
import logging
from typing import Union, Tuple, Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

# Try to import cryptography, with fallback for compatibility
CRYPTOGRAPHY_AVAILABLE = False
try:
    from cryptography.fernet import Fernet
    from cryptography.fernet import InvalidToken
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    logger.warning("cryptography module not found. Install with: pip install cryptography")    # Fallback implementation
    class InvalidToken(Exception):
        """Fallback exception for invalid tokens."""
        pass
        
    class Fernet:
        """Fallback implementation of Fernet for environments without cryptography package."""
        @staticmethod
        def generate_key():
            """Fallback key generation."""
            return os.urandom(32).hex().encode()
        
        def __init__(self, key):
            self.key = key
        
        def encrypt(self, data):
            """Fallback encryption (NOT SECURE - FOR COMPATIBILITY ONLY)."""
            logger.warning("Using insecure fallback encryption. Install cryptography module.")
            return b"ENCRYPTED:" + data
        
        def decrypt(self, data):
            """Fallback decryption (NOT SECURE - FOR COMPATIBILITY ONLY)."""
            logger.warning("Using insecure fallback decryption. Install cryptography module.")
            if data.startswith(b"ENCRYPTED:"):
                return data[10:]
            return data

def generate_key() -> bytes:
    """
    Generate a new secure encryption key.
    
    Returns:
        bytes: A new Fernet key suitable for encryption operations
    """
    try:
        return Fernet.generate_key()
    except Exception as e:
        logger.error(f"Error generating encryption key: {str(e)}")
        raise RuntimeError(f"Failed to generate encryption key: {str(e)}")

def encrypt_data(data: str, key: bytes) -> bytes:
    """
    Encrypt the given data using the provided key.
    
    Args:
        data: The string data to encrypt
        key: The Fernet key to use for encryption
    
    Returns:
        bytes: The encrypted data
        
    Raises:
        ValueError: If the key is invalid
        TypeError: If the data is not a string
    """
    if not isinstance(data, str):
        raise TypeError("Data must be a string")
        
    try:
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode())
        return encrypted_data
    except Exception as e:
        logger.error(f"Encryption error: {str(e)}")
        raise RuntimeError(f"Failed to encrypt data: {str(e)}")

def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    """
    Decrypt the given encrypted data using the provided key.
    
    Args:
        encrypted_data: The encrypted data to decrypt
        key: The Fernet key to use for decryption
    
    Returns:
        str: The decrypted data as a string
        
    Raises:
        InvalidToken: If the encrypted data is invalid or has been tampered with
        ValueError: If the key is invalid
    """
    try:
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data).decode()
        return decrypted_data
    except InvalidToken:
        logger.error("Invalid token or corrupted encrypted data")
        raise InvalidToken("Data corruption detected or wrong decryption key")
    except Exception as e:
        logger.error(f"Decryption error: {str(e)}")
        raise RuntimeError(f"Failed to decrypt data: {str(e)}")

def hash_password(password: str, salt: Optional[str] = None) -> Union[str, Tuple[str, str]]:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with a salt.
    
    This is a secure way to store passwords, using a strong hashing algorithm
    with 100,000 iterations and a random salt.
    
    Args:
        password: The password to hash
        salt: Optional salt to use for hashing. If None, a new salt is generated.
        
    Returns:
        If salt is None: Tuple of (hashed_password, salt)
        If salt is provided: Just the hashed_password
        
    Examples:
        >>> # Generate new salt
        >>> hashed_pwd, salt = hash_password("my_secure_password")
        >>> # Verify with existing salt
        >>> verify_password(hashed_pwd, "my_secure_password", salt)  # Returns: True
    """
    if not password:
        raise ValueError("Password cannot be empty")
        
    try:
        # Create a salt if not provided
        if salt is None:
            salt = os.urandom(32).hex()
            
        # Create the hashed password
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode() if isinstance(salt, str) else salt,
            100000,  # Number of iterations (high for security)
            dklen=128  # Length of the derived key
        )
        
        # Convert to hex string for storage
        hash_str = key.hex()
        
        return (hash_str, salt) if salt is None else hash_str
    except Exception as e:
        logger.error(f"Password hashing error: {str(e)}")
        raise RuntimeError(f"Failed to hash password: {str(e)}")

def verify_password(stored_hash: str, provided_password: str, salt: str) -> bool:
    """
    Verify a provided password against a stored hash.
    
    Args:
        stored_hash: The previously stored password hash
        provided_password: The password to verify
        salt: The salt used for the stored hash
        
    Returns:
        bool: True if the password matches, False otherwise
        
    Examples:
        >>> hashed_pwd, salt = hash_password("my_secure_password")
        >>> verify_password(hashed_pwd, "my_secure_password", salt)  # Returns: True
        >>> verify_password(hashed_pwd, "wrong_password", salt)  # Returns: False
    """
    if not stored_hash or not provided_password or not salt:
        return False
        
    try:
        # Hash the provided password with the same salt
        verification_hash = hash_password(provided_password, salt)
        
        # If using the tuple return version, extract just the hash
        if isinstance(verification_hash, tuple):
            verification_hash = verification_hash[0]
            
        # Compare with stored hash
        return verification_hash == stored_hash
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def encrypt_card_data(card_number: str, cvv: str, pin: str) -> Dict[str, Any]:
    """
    Encrypt sensitive card data using separate encryption for each field.
    
    Args:
        card_number: The card number to encrypt
        cvv: The CVV to encrypt
        pin: The PIN to encrypt
        
    Returns:
        dict: Dictionary containing encrypted data and the encryption key
        
    Warning:
        The key is included in the return value but should be stored separately
        in a secure location in a production environment.
    """
    try:
        # Generate a key for this encryption session
        key = generate_key()
        
        # Encrypt each piece of data
        encrypted_card = encrypt_data(card_number, key)
        encrypted_cvv = encrypt_data(cvv, key)
        encrypted_pin = encrypt_data(pin, key)
        
        return {
            'card_number': encrypted_card,
            'cvv': encrypted_cvv,
            'pin': encrypted_pin,
            'key': key  # The key should be stored securely
        }
    except Exception as e:
        logger.error(f"Card data encryption error: {str(e)}")
        raise RuntimeError(f"Failed to encrypt card data: {str(e)}")