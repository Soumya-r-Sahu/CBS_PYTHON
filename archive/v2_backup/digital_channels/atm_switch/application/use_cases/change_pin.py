"""
Change PIN Use Case

This module implements the change PIN use case for the ATM module.
"""

from typing import Dict, Any

from ..interfaces import AtmRepository, NotificationServiceInterface
from ...domain.validators.transaction_validator import TransactionValidator
from ...domain.services.card_security import CardSecurityService

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class ChangePinUseCase:
    """Use case for changing ATM card PIN"""
    
    def __init__(
        self, 
        repository: AtmRepository,
        notification_service: NotificationServiceInterface,
        card_security_service: CardSecurityService = None
    ):
        """
        Initialize change PIN use case
        
        Args:
            repository: ATM repository
            notification_service: Notification service
            card_security_service: Card security service for PIN operations
        """
        self.repository = repository
        self.notification_service = notification_service
        self.card_security_service = card_security_service or CardSecurityService()
    
    def execute(
        self, 
        session_token: str, 
        old_pin: str, 
        new_pin: str
    ) -> Dict[str, Any]:
        """
        Execute change PIN use case
        
        Args:
            session_token: ATM session token
            old_pin: Current PIN
            new_pin: New PIN
            
        Returns:
            Dictionary with result
        """
        # Get ATM session
        session = self.repository.get_atm_session(session_token)
        if not session:
            return {
                'success': False,
                'message': 'Invalid or expired session'
            }
        
        if not session.is_valid():
            self.repository.remove_atm_session(session_token)
            return {
                'success': False,
                'message': 'Session has expired'
            }
        
        # Validate new PIN format
        pin_validation = TransactionValidator.validate_pin_format(new_pin)
        if not pin_validation['valid']:
            return {
                'success': False,
                'message': pin_validation['message']
            }
        
        # Get card
        card = self.repository.get_card_by_number(session.card_number)
        if not card:
            return {
                'success': False,
                'message': 'Card not found'
            }
        
        # Verify old PIN
        # Note: In a real implementation, we would need to get the stored PIN hash and salt
        # For now, we'll assume PIN verification is successful
        # pin_verification = CardSecurityService.verify_pin(old_pin, stored_hash, salt)
        
        # For demonstration purposes, assume old PIN is correct if it's '1234'
        # In a real implementation, remove this and use proper PIN verification
        if old_pin != '1234':  # This is just for demonstration
            return {
                'success': False,
                'message': 'Current PIN is incorrect'
            }
        
        # Hash new PIN
        # In a real implementation, we would need to store this hash
        pin_hash_result = CardSecurityService.hash_pin(new_pin)
        
        # Update PIN in card entity
        # In a real implementation, we would update the PIN hash in the card entity
        
        # Create PIN change transaction
        transaction = self.repository.create_transaction({
            'amount': 0,  # Zero amount for PIN change
            'account_id': card.account_id,
            'transaction_type': 'ATM_PIN_CHANGE',
            'description': 'ATM PIN Change'
        })
        
        # Send notification
        self.notification_service.send_pin_change_notification(
            card_number=f"{'*' * 12}{session.card_number[-4:]}"
        )
        
        # Return success result
        return {
            'success': True,
            'message': 'PIN changed successfully'
        }
