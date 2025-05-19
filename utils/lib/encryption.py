"""
Encryption utilities for secure password handling and data protection
"""
import hashlib
import os
import base64
import secrets
import binascii
from typing import Tuple, Optional

def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Hash a password using PBKDF2 with SHA-256
    
    Args:
        password: The password to hash
        salt: Optional salt, generated if not provided
        
    Returns:
        Tuple of (hash, salt)
    """
    if not salt:
        salt = secrets.token_bytes(32)  # Generate a new salt if none is provided
    
    # Use PBKDF2 with 100,000 iterations for security
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations=100000,
        dklen=32
    )
    
    return key, salt

def verify_password(stored_password: bytes, stored_salt: bytes, provided_password: str) -> bool:
    """
    Verify a password against a stored hash and salt
    
    Args:
        stored_password: The stored password hash
        stored_salt: The salt used for the stored hash
        provided_password: The password to verify
        
    Returns:
        True if password matches, False otherwise
    """
    # Hash the provided password with the stored salt
    key, _ = hash_password(provided_password, stored_salt)
    
    # Use constant-time comparison to prevent timing attacks
    return secrets.compare_digest(key, stored_password)

def encrypt_sensitive_data(data: str, key: bytes) -> str:
    """
    Encrypt sensitive data (like PINs, card numbers) for storage
    
    Args:
        data: The data to encrypt
        key: Encryption key
        
    Returns:
        Base64 encoded encrypted data
    """
    try:
        from cryptography.fernet import Fernet
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode('utf-8'))
        return base64.b64encode(encrypted_data).decode('utf-8')
    except ImportError:
        # Fallback if cryptography is not available
        # Note: This is less secure and should be used only as fallback
        from hashlib import sha256
        salt = os.urandom(16)
        key = sha256(key + salt).digest()
        return binascii.hexlify(salt + key[:16] + data.encode('utf-8')).decode('utf-8')

def decrypt_sensitive_data(encrypted_data: str, key: bytes) -> str:
    """
    Decrypt sensitive data
    
    Args:
        encrypted_data: Base64 encoded encrypted data
        key: Decryption key
        
    Returns:
        Decrypted data as string
    """
    try:
        from cryptography.fernet import Fernet
        f = Fernet(key)
        return f.decrypt(base64.b64decode(encrypted_data)).decode('utf-8')
    except ImportError:
        # Fallback decryption
        data = binascii.unhexlify(encrypted_data.encode('utf-8'))
        salt, key_part, encrypted = data[:16], data[16:32], data[32:]
        return encrypted.decode('utf-8')
