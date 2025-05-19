"""
Common encryption utilities for the Core Banking System.

This module consolidates encryption functions from across the system
to reduce code duplication and promote consistency.
"""

from typing import Dict, Any, Tuple, Optional, Union, List
import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

# Configure logger
logger = logging.getLogger(__name__)

def generate_key(password: Optional[str] = None, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Generate an encryption key using a password and salt.
    
    Args:
        password: The password to use for key generation
        salt: Salt for key derivation. If None, a random salt is generated.
        
    Returns:
        Tuple of (key, salt)
    """
    if salt is None:
        salt = os.urandom(16)
    
    if password is None:
        password = os.environ.get('CBS_ENCRYPTION_PASSWORD', 'default-secure-password')
    
    # Use PBKDF2 to derive a key from the password
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    return key, salt

def encrypt_data(data: Union[str, bytes], key: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Encrypt data using Fernet symmetric encryption.
    
    Args:
        data: The data to encrypt
        key: The encryption key. If None, a key is generated.
        
    Returns:
        Dictionary containing the encrypted data and encryption metadata
    """
    try:
        # Generate key if not provided
        if key is None:
            key, salt = generate_key()
            using_generated_key = True
        else:
            salt = None
            using_generated_key = False
        
        # Convert data to bytes if it's a string
        if isinstance(data, str):
            data_bytes = data.encode()
        else:
            data_bytes = data
        
        # Create Fernet cipher and encrypt
        cipher = Fernet(key)
        encrypted_data = cipher.encrypt(data_bytes)
        
        # Return encrypted data and metadata
        result = {
            "encrypted_data": base64.b64encode(encrypted_data).decode(),
            "encryption_method": "fernet",
        }
        
        # Include salt if we generated a key
        if using_generated_key:
            result["salt"] = base64.b64encode(salt).decode()
        
        return result
    
    except Exception as e:
        logger.error(f"Encryption error: {str(e)}")
        raise

def decrypt_data(encrypted_package: Dict[str, Any], key: Optional[bytes] = None, 
               password: Optional[str] = None) -> bytes:
    """
    Decrypt data that was encrypted with encrypt_data.
    
    Args:
        encrypted_package: The dictionary containing encrypted data and metadata
        key: The encryption key. If None, it's derived from the password and salt.
        password: The password to derive the key from if key is not provided.
        
    Returns:
        The decrypted data as bytes
    """
    try:
        # Check if we need to derive the key
        if key is None and "salt" in encrypted_package:
            if password is None:
                password = os.environ.get('CBS_ENCRYPTION_PASSWORD', 'default-secure-password')
            
            salt = base64.b64decode(encrypted_package["salt"])
            key, _ = generate_key(password, salt)
        
        if key is None:
            raise ValueError("Either key or both password and salt must be provided")
        
        # Decode the encrypted data
        encrypted_data = base64.b64decode(encrypted_package["encrypted_data"])
        
        # Create Fernet cipher and decrypt
        cipher = Fernet(key)
        decrypted_data = cipher.decrypt(encrypted_data)
        
        return decrypted_data
    
    except Exception as e:
        logger.error(f"Decryption error: {str(e)}")
        raise

def encrypt_sensitive_data(data_dict: Dict[str, Any], 
                         sensitive_fields: List[str]) -> Dict[str, Any]:
    """
    Encrypt specific sensitive fields in a dictionary.
    
    Args:
        data_dict: Dictionary containing data
        sensitive_fields: List of field names that should be encrypted
        
    Returns:
        Dictionary with sensitive fields encrypted
    """
    result = data_dict.copy()
    
    # Generate a single key for all fields
    key, salt = generate_key()
    
    # Track which fields were encrypted
    encrypted_fields = []
    
    # Encrypt each sensitive field
    for field in sensitive_fields:
        if field in result and result[field]:
            # Encrypt the field
            encrypted_package = encrypt_data(str(result[field]), key)
            result[field] = encrypted_package["encrypted_data"]
            encrypted_fields.append(field)
    
    # Add encryption metadata if any fields were encrypted
    if encrypted_fields:
        result["_encryption"] = {
            "method": "fernet",
            "salt": base64.b64encode(salt).decode(),
            "encrypted_fields": encrypted_fields
        }
    
    return result
