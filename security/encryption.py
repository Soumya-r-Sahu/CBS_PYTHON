"""
Core Banking System - Security Encryption Module

This module provides centralized encryption functionality for the Core Banking System.
It simplifies the interface to the encryption utilities.
"""

import logging
from typing import Union, Optional, Any

# Import the actual implementation from the encryption package
from security.common.encryption import encrypt_text, decrypt_text

# Configure logger
logger = logging.getLogger(__name__)


def encrypt_data(data: Union[str, bytes, dict, list], key: Optional[str] = None) -> Union[str, dict, list]:
    """
    Encrypt data with optional key
    
    This is a high-level wrapper for the encryption implementation.
    
    Args:
        data: Data to encrypt (string, bytes, dict or list)
        key: Optional encryption key
        
    Returns:
        Encrypted data in the same format as input
    """
    try:
        # Handle different data types
        if isinstance(data, (dict, list)):
            import json
            # Convert to JSON string, encrypt, and return
            json_str = json.dumps(data)
            return encrypt_text(json_str, key)
        elif isinstance(data, str):
            return encrypt_text(data, key)
        elif isinstance(data, bytes):
            return encrypt_text(data.decode('utf-8'), key)
        else:
            raise TypeError(f"Unsupported data type for encryption: {type(data)}")
            
    except Exception as e:
        logger.error(f"Encryption error: {str(e)}")
        raise


def decrypt_data(encrypted_data: str, key: Optional[str] = None, output_type: str = 'auto') -> Any:
    """
    Decrypt data with optional key
    
    This is a high-level wrapper for the decryption implementation.
    
    Args:
        encrypted_data: Encrypted data string
        key: Optional decryption key
        output_type: Output format ('auto', 'str', 'dict', 'list', 'bytes')
        
    Returns:
        Decrypted data in the requested format
    """
    try:
        # Decrypt the data
        decrypted = decrypt_text(encrypted_data, key)
        
        # Handle output format
        if output_type == 'str' or output_type == 'auto':
            # Try to detect JSON
            if output_type == 'auto' and (
                (decrypted.startswith('{') and decrypted.endswith('}')) or
                (decrypted.startswith('[') and decrypted.endswith(']'))
            ):
                try:
                    import json
                    return json.loads(decrypted)
                except json.JSONDecodeError:
                    # Not valid JSON, return as string
                    return decrypted
            return decrypted
        elif output_type == 'dict':
            import json
            return json.loads(decrypted)
        elif output_type == 'list':
            import json
            return json.loads(decrypted)
        elif output_type == 'bytes':
            return decrypted.encode('utf-8')
        else:
            raise ValueError(f"Unsupported output type: {output_type}")
            
    except Exception as e:
        logger.error(f"Decryption error: {str(e)}")
        raise
