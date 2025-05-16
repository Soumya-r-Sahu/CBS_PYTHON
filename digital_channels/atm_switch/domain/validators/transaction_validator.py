"""
Transaction Validator

This module defines the transaction validation logic for the ATM system.
"""

from decimal import Decimal
from typing import Dict, Any

class TransactionValidator:
    """Validator for ATM transactions"""
    
    @staticmethod
    def validate_withdrawal_amount(amount: Decimal, min_withdrawal: Decimal, max_withdrawal: Decimal) -> Dict[str, Any]:
        """
        Validate withdrawal amount
        
        Args:
            amount: Amount to withdraw
            min_withdrawal: Minimum withdrawal limit
            max_withdrawal: Maximum withdrawal limit
            
        Returns:
            Dictionary with validation result
        """
        if amount <= Decimal('0'):
            return {
                'valid': False,
                'message': 'Withdrawal amount must be greater than zero'
            }
            
        if amount < min_withdrawal:
            return {
                'valid': False,
                'message': f'Amount must be at least {min_withdrawal}'
            }
            
        if amount > max_withdrawal:
            return {
                'valid': False,
                'message': f'Amount cannot exceed {max_withdrawal}'
            }
            
        return {'valid': True}
    
    @staticmethod
    def validate_denomination(amount: Decimal, denomination: Decimal = Decimal('100')) -> Dict[str, Any]:
        """
        Validate if amount is in valid denominations
        
        Args:
            amount: Amount to validate
            denomination: Denomination value (default 100 INR)
            
        Returns:
            Dictionary with validation result
        """
        if amount % denomination != Decimal('0'):
            return {
                'valid': False,
                'message': f'Amount must be in multiples of {denomination}'
            }
            
        return {'valid': True}
    
    @staticmethod
    def validate_daily_limit(
        current_amount: Decimal, 
        todays_withdrawals: Decimal, 
        daily_limit: Decimal
    ) -> Dict[str, Any]:
        """
        Validate daily withdrawal limit
        
        Args:
            current_amount: Current withdrawal amount
            todays_withdrawals: Total withdrawals made today
            daily_limit: Daily withdrawal limit
            
        Returns:
            Dictionary with validation result
        """
        if todays_withdrawals + current_amount > daily_limit:
            return {
                'valid': False,
                'message': f'Daily withdrawal limit of {daily_limit} would be exceeded'
            }
            
        return {'valid': True}
    
    @staticmethod
    def validate_pin_format(pin: str) -> Dict[str, Any]:
        """
        Validate PIN format
        
        Args:
            pin: PIN to validate
            
        Returns:
            Dictionary with validation result
        """
        if not pin or not isinstance(pin, str):
            return {
                'valid': False,
                'message': 'PIN must be a string'
            }
            
        if not pin.isdigit():
            return {
                'valid': False,
                'message': 'PIN must contain only digits'
            }
            
        if len(pin) != 4:
            return {
                'valid': False,
                'message': 'PIN must be exactly 4 digits'
            }
            
        return {'valid': True}
