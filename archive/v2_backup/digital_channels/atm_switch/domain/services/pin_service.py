"""
PIN Service

This module defines PIN-related services for the ATM domain.
"""

import hashlib
import os
from typing import Dict, Any

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class PinService:
    """Service for handling PIN operations"""
    
    @staticmethod
    def hash_pin(pin: str, salt: str = None) -> Dict[str, str]:
        """
        Hash a PIN with salt for secure storage
        
        Args:
            pin: The PIN to hash
            salt: Optional salt value, generated if not provided
            
        Returns:
            Dictionary containing hash and salt
        """
        if not salt:
            salt = os.urandom(32).hex()  # Generate a random salt
        
        # Create hash with pin and salt
        pin_hash = hashlib.pbkdf2_hmac(
            'sha256',
            pin.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # Number of iterations
        ).hex()
        
        return {
            'hash': pin_hash,
            'salt': salt
        }
    
    @staticmethod
    def verify_pin(entered_pin: str, stored_hash: str, salt: str) -> bool:
        """
        Verify a PIN against stored hash
        
        Args:
            entered_pin: PIN entered by user
            stored_hash: Stored hash value
            salt: Salt used in hashing
            
        Returns:
            True if PIN is correct, False otherwise
        """
        # Generate hash with entered pin and stored salt
        pin_hash = hashlib.pbkdf2_hmac(
            'sha256',
            entered_pin.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # Number of iterations
        ).hex()
        
        # Compare with stored hash
        return pin_hash == stored_hash
    
    @staticmethod
    def validate_pin_format(pin: str) -> Dict[str, Any]:
        """
        Validate PIN format
        
        Args:
            pin: PIN to validate
            
        Returns:
            Dictionary with validation result
        """
        # PIN must be exactly 4 digits
        if len(pin) != 4:
            return {
                'valid': False,
                'message': 'PIN must be exactly 4 digits'
            }
        
        # PIN must be numeric
        if not pin.isdigit():
            return {
                'valid': False,
                'message': 'PIN must contain only digits'
            }
        
        # PIN should not be a simple sequence or repeated digits
        simple_patterns = ['0000', '1111', '2222', '3333', '4444', '5555', 
                          '6666', '7777', '8888', '9999', '1234', '4321']
        
        if pin in simple_patterns:
            return {
                'valid': False,
                'message': 'PIN is too simple'
            }
        
        # PIN is valid
        return {'valid': True}
