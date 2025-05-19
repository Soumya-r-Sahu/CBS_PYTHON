"""
Check Balance Use Case

This module implements the check balance use case for the ATM module.
"""

from typing import Dict, Any

from ..interfaces import AtmRepository, NotificationServiceInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class CheckBalanceUseCase:
    """Use case for checking account balance via ATM"""
    
    def __init__(
        self, 
        repository: AtmRepository,
        notification_service: NotificationServiceInterface
    ):
        """
        Initialize check balance use case
        
        Args:
            repository: ATM repository
            notification_service: Notification service
        """
        self.repository = repository
        self.notification_service = notification_service
    
    def execute(self, session_token: str) -> Dict[str, Any]:
        """
        Execute check balance use case
        
        Args:
            session_token: ATM session token
            
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
        
        # Get account
        account = self.repository.get_account_by_id(session.account_id)
        
        if not account:
            return {
                'success': False,
                'message': 'Account not found'
            }
        
        # Check if account is active
        if not account.is_active():
            return {
                'success': False,
                'message': f'Account is {account.status.lower()}'
            }
        
        # Create balance inquiry transaction
        transaction = self.repository.create_transaction({
            'amount': 0,  # Zero amount for inquiry
            'account_id': account.account_id,
            'transaction_type': 'ATM_INQUIRY',
            'description': 'ATM Balance Inquiry',
            'balance_before': account.balance,
            'balance_after': account.balance
        })
        
        # Send notification
        self.notification_service.send_balance_inquiry_notification(
            account_number=account.account_number,
            balance=account.balance
        )
        
        # Return success result
        return {
            'success': True,
            'account_number': account.account_number,
            'balance': str(account.balance),
            'available_balance': str(account.balance),  # In a real system, these might differ
            'currency': account.currency,
            'datetime': transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S') if transaction else None
        }
