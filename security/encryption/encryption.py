"""
Encryption Module for Core Banking System

This module provides encryption and decryption functionalities for sensitive data.
It uses industry-standard algorithms for secure data protection.
"""

import os
import base64
import logging
from typing import Tuple, Union, Optional
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# Configure logger
logger = logging.getLogger(__name__)

# Default encryption key (in production, this should be stored securely)
DEFAULT_KEY = os.environ.get("ENCRYPTION_KEY", "default_encryption_key_for_development_only")


def generate_key(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Generate an encryption key from a password using PBKDF2.
    
    Args:
        password (str): The password to derive the key from
        salt (bytes, optional): Salt to use, if None a new salt is generated
        
    Returns:
        Tuple[bytes, bytes]: (key, salt)
    """
    if salt is None:
        salt = os.urandom(16)
    
    # Use PBKDF2 to derive a key from the password
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 32 bytes = 256 bits
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return key, salt


def encrypt(data: Union[str, bytes], key: bytes) -> bytes:
    """
    Encrypt data using AES encryption.

    Args:
        data (Union[str, bytes]): The data to encrypt
        key (bytes): The encryption key

    Returns:
        bytes: The encrypted data
    """
    if isinstance(data, str):
        data = data.encode()

    # Pad the data to be AES block size compliant
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()

    # Encrypt the data
    iv = os.urandom(16)  # Initialization vector
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Return the IV and encrypted data as a single byte string
    return base64.b64encode(iv + encrypted_data)


def decrypt(encrypted_data: bytes, key: bytes) -> bytes:
    """
    Decrypt data using AES encryption.

    Args:
        encrypted_data (bytes): The encrypted data to decrypt
        key (bytes): The encryption key

    Returns:
        bytes: The decrypted data
    """
    encrypted_data = base64.b64decode(encrypted_data)

    # Extract the IV and encrypted data
    iv = encrypted_data[:16]
    encrypted_data = encrypted_data[16:]

    # Decrypt the data
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

    # Remove padding
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()

    return data


def encrypt_text(text: str, key: Optional[str] = None) -> str:
    """
    Encrypt a text string and return a formatted encrypted string.
    
    Args:
        text (str): Text to encrypt
        key (str, optional): Encryption key
        
    Returns:
        str: Formatted encrypted text
    """
    try:
        encryption_key, _ = generate_key(key or DEFAULT_KEY)
        encrypted = encrypt(text, encryption_key)
        return encrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Error encrypting text: {str(e)}")
        raise


def decrypt_text(encrypted_text: str, key: Optional[str] = None) -> str:
    """
    Decrypt a formatted encrypted string back to text.
    
    Args:
        encrypted_text (str): Formatted encrypted text
        key (str, optional): Encryption key
        
    Returns:
        str: Original decrypted text
    """
    try:
        encryption_key, _ = generate_key(key or DEFAULT_KEY)
        decrypted_bytes = decrypt(encrypted_text.encode('utf-8'), encryption_key)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Error decrypting text: {str(e)}")
        raise


if __name__ == "__main__":
    # Example usage
    secret_message = "This is a secret banking transaction detail"
    
    # Encrypt
    encrypted_text = encrypt_text(secret_message)
    print(f"Encrypted: {encrypted_text}")
    
    # Decrypt
    decrypted_text = decrypt_text(encrypted_text)
    print(f"Decrypted: {decrypted_text}")
    
    # Verify
    print(f"Original text matches decrypted: {secret_message == decrypted_text}")
