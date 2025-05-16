"""
Validate Card Use Case

This module implements the validate card use case for the ATM module.
"""

from typing import Dict, Any

from ..interfaces import AtmRepository
from ...domain.entities import AtmSession
from ...domain.validators import CardValidator
from ...domain.services import CardSecurityService


class ValidateCardUseCase:
    """Use case for validating ATM cards"""
    
    def __init__(self, repository: AtmRepository):
        """
        Initialize validate card use case
        
        Args:
            repository: ATM repository
        """
        self.repository = repository
    
    def execute(self, card_number: str, pin: str) -> Dict[str, Any]:
        """
        Execute validate card use case
        
        Args:
            card_number: Card number to validate
            pin: PIN to validate
            
        Returns:
            Dictionary with validation result
        """
        # Validate card number format
        card_validation = CardValidator.validate_card_number(card_number)
        if not card_validation['valid']:
            return {
                'valid': False,
                'message': card_validation['message']
            }
        
        # Get card from repository
        card = self.repository.get_card_by_number(card_number)
        if not card:
            return {
                'valid': False,
                'message': 'Card not found'
            }
        
        # Validate card status
        card_status = CardSecurityService.validate_card_status(card)
        if not card_status['valid']:
            return {
                'valid': False,
                'message': card_status['message']
            }
        
        # Get account
        account = self.repository.get_account_by_id(card.account_id)
        if not account:
            return {
                'valid': False,
                'message': 'Account not found'
            }
        
        # Check if account is active
        if not account.is_active():
            return {
                'valid': False,
                'message': f'Account is {account.status.lower()}'
            }
        
        # Verify PIN
        # Note: In a real implementation, we would need to get the stored PIN hash and salt
        # For now, we'll assume PIN verification is successful
        # pin_verification = CardSecurityService.verify_pin(pin, stored_hash, salt)
        
        # For demonstration purposes, assume PIN is correct if it's '1234'
        # In a real implementation, remove this and use proper PIN verification
        if pin != '1234':  # This is just for demonstration
            # Process failed PIN attempt
            result = CardSecurityService.process_failed_pin_attempt(card)
            
            # Update card status
            self.repository.update_card_status(card)
            
            return {
                'valid': False,
                'message': result['message']
            }
        
        # Reset failed attempts
        CardSecurityService.reset_failed_attempts(card)
        
        # Update card
        self.repository.update_card_status(card)
        
        # Create session
        session = AtmSession.create(
            card_number=card.card_number,
            account_id=account.account_id
        )
        
        # Store session
        self.repository.store_atm_session(session)
        
        # Record card usage
        card.record_usage()
        self.repository.update_card_status(card)
        
        # Return successful validation result
        return {
            'valid': True,
            'session_token': session.session_token,
            'account_number': account.account_number,
            'card_number_masked': f"{'*' * 12}{card_number[-4:]}",
            'account_type': account.account_type,
            'customer_name': 'John Doe'  # In real implementation, get from customer repository
        }
