"""
Card Validator

This module defines the card validation logic for the ATM system.
"""

import re
from typing import Dict, Any
from datetime import datetime

class CardValidator:
    """Validator for ATM cards"""
    
    @staticmethod
    def validate_card_number(card_number: str) -> Dict[str, Any]:
        """
        Validate card number format
        
        Args:
            card_number: Card number to validate
            
        Returns:
            Dictionary with validation result
        """
        if not card_number or not isinstance(card_number, str):
            return {
                'valid': False,
                'message': 'Card number must be a string'
            }
            
        # Remove spaces and dashes for validation
        clean_number = card_number.replace(' ', '').replace('-', '')
        
        if not clean_number.isdigit():
            return {
                'valid': False,
                'message': 'Card number must contain only digits'
            }
            
        if not (13 <= len(clean_number) <= 19):
            return {
                'valid': False,
                'message': 'Card number must be 13-19 digits long'
            }
            
        # Luhn algorithm check (basic credit card validation)
        if not CardValidator.luhn_check(clean_number):
            return {
                'valid': False,
                'message': 'Invalid card number'
            }
            
        return {'valid': True}
    
    @staticmethod
    def validate_expiry_date(expiry_date: datetime) -> Dict[str, Any]:
        """
        Validate if card is expired
        
        Args:
            expiry_date: Card expiry date
            
        Returns:
            Dictionary with validation result
        """
        if datetime.now() >= expiry_date:
            return {
                'valid': False,
                'message': 'Card has expired'
            }
            
        return {'valid': True}
    
    @staticmethod
    def validate_card_status(status: str) -> Dict[str, Any]:
        """
        Validate card status
        
        Args:
            status: Card status
            
        Returns:
            Dictionary with validation result
        """
        if status != "ACTIVE":
            return {
                'valid': False,
                'message': f'Card is {status.lower()}'
            }
            
        return {'valid': True}
    
    @staticmethod
    def luhn_check(card_number: str) -> bool:
        """
        Implement Luhn algorithm for credit card validation
        
        Args:
            card_number: Card number to validate
            
        Returns:
            True if valid, False otherwise
        """
        digits = [int(d) for d in card_number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for digit in even_digits:
            checksum += sum(divmod(digit * 2, 10))
        return checksum % 10 == 0
