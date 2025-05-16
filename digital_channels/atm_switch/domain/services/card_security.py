"""
Card Security Service

This module defines core security logic for ATM cards.
"""

import hashlib
import hmac
import os
from typing import Dict, Any, Optional

from ..entities import AtmCard


class CardSecurityService:
    """Core security logic for ATM cards"""
    
    @staticmethod
    def hash_pin(pin: str, salt: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Hash PIN using secure hashing algorithm
        
        Args:
            pin: PIN to hash
            salt: Optional salt (generated if not provided)
            
        Returns:
            Dictionary with hash and salt
        """
        if salt is None:
            salt = os.urandom(32)  # Generate random salt
        
        # Use HMAC with SHA-256 for secure PIN hashing
        key = hashlib.pbkdf2_hmac(
            hash_name='sha256',
            password=pin.encode('utf-8'),
            salt=salt,
            iterations=100000  # High iteration count for security
        )
        
        return {
            'hash': key,
            'salt': salt
        }
    
    @staticmethod
    def verify_pin(pin: str, stored_hash: bytes, salt: bytes) -> bool:
        """
        Verify PIN against stored hash
        
        Args:
            pin: PIN to verify
            stored_hash: Previously stored PIN hash
            salt: Salt used for hashing
            
        Returns:
            True if PIN is valid, False otherwise
        """
        verification_result = CardSecurityService.hash_pin(pin, salt)
        return hmac.compare_digest(verification_result['hash'], stored_hash)
    
    @staticmethod
    def validate_card_status(card: AtmCard) -> Dict[str, Any]:
        """
        Validate if a card is usable
        
        Args:
            card: Card to validate
            
        Returns:
            Dictionary with validation result
        """
        # Check if card is expired
        if card.is_expired():
            return {
                'valid': False,
                'message': 'Card has expired'
            }
        
        # Check if card is blocked
        if card.is_blocked():
            return {
                'valid': False,
                'message': 'Card is blocked due to multiple failed attempts'
            }
        
        # Check if card is active
        if not card.is_valid():
            return {
                'valid': False,
                'message': f'Card is {card.status.lower()}'
            }
        
        return {
            'valid': True,
            'message': 'Card is valid'
        }
    
    @staticmethod
    def process_failed_pin_attempt(card: AtmCard) -> Dict[str, Any]:
        """
        Process failed PIN attempt and update card status
        
        Args:
            card: Card to update
            
        Returns:
            Dictionary with updated card status
        """
        card.increment_failed_attempts()
        
        if card.is_blocked():
            return {
                'status': 'BLOCKED',
                'attempts_remaining': 0,
                'message': 'Card has been blocked due to multiple failed attempts'
            }
        
        attempts_remaining = 3 - card.failed_pin_attempts
        return {
            'status': card.status,
            'attempts_remaining': attempts_remaining,
            'message': f'Invalid PIN. {attempts_remaining} attempts remaining.'
        }
    
    @staticmethod
    def reset_failed_attempts(card: AtmCard) -> None:
        """
        Reset failed PIN attempts after successful validation
        
        Args:
            card: Card to update
        """
        if card.failed_pin_attempts > 0:
            card.reset_failed_attempts()
