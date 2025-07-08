"""
UPI Transaction rules service.
Contains business rules for UPI transactions.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from ..entities.upi_transaction import UpiTransaction, UpiTransactionStatus


class UpiTransactionRulesService:
    """Encapsulates business rules and validations for UPI transactions."""
    
    def __init__(self, daily_transaction_limit: float = 100000.0, 
                 per_transaction_limit: float = 25000.0):
        """
        Initialize with transaction limits.
        
        Args:
            daily_transaction_limit: Maximum amount allowed per day per user
            per_transaction_limit: Maximum amount allowed per transaction
        """
        self.daily_transaction_limit = daily_transaction_limit
        self.per_transaction_limit = per_transaction_limit
    
    def validate_transaction(self, transaction: UpiTransaction, 
                             daily_total: float = 0.0) -> Dict[str, Any]:
        """
        Validate a UPI transaction according to business rules.
        
        Args:
            transaction: The UPI transaction to validate
            daily_total: Total amount of transactions for the sender on this day
            
        Returns:
            A dictionary with validation result: 
            {
                'is_valid': bool,
                'message': Optional[str]
            }
        """
        # Check transaction amount limit
        if transaction.amount > self.per_transaction_limit:
            return {
                'is_valid': False,
                'message': f"Transaction amount exceeds the limit of {self.per_transaction_limit}"
            }
        
        # Check daily transaction limit
        if daily_total + transaction.amount > self.daily_transaction_limit:
            return {
                'is_valid': False,
                'message': f"Daily transaction limit of {self.daily_transaction_limit} would be exceeded"
            }
        
        # Check sender and receiver are not the same
        if transaction.sender_vpa == transaction.receiver_vpa:
            return {
                'is_valid': False,
                'message': "Cannot send money to the same account"
            }
        
        # Check transaction has not expired (30 minutes)
        transaction_age = datetime.now() - transaction.transaction_date
        if transaction_age > timedelta(minutes=30):
            return {
                'is_valid': False,
                'message': "Transaction request has expired"
            }
        
        # All validations passed
        return {
            'is_valid': True,
            'message': None
        }
    
    def can_reverse_transaction(self, transaction: UpiTransaction) -> Dict[str, Any]:
        """
        Check if a transaction can be reversed.
        
        Args:
            transaction: The UPI transaction to check
            
        Returns:
            A dictionary with the result: 
            {
                'can_reverse': bool,
                'message': Optional[str]
            }
        """
        # Can only reverse completed transactions
        if transaction.status != UpiTransactionStatus.COMPLETED:
            return {
                'can_reverse': False,
                'message': f"Cannot reverse transaction with status: {transaction.status}"
            }
        
        # Check if the transaction is within the reversible time frame (24 hours)
        transaction_age = datetime.now() - transaction.transaction_date
        if transaction_age > timedelta(hours=24):
            return {
                'can_reverse': False,
                'message': "Transactions can only be reversed within 24 hours"
            }
        
        return {
            'can_reverse': True,
            'message': None
        }
