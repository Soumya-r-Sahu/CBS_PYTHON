"""
Transaction Rules Service

Provides domain services for transaction validation and business rules.
"""
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..entities.transaction import Transaction, TransactionType

class TransactionRulesService:
    """Domain service for transaction business rules"""
    
    def __init__(self, 
                 withdrawal_daily_limit: Decimal = Decimal('50000'),
                 transfer_daily_limit: Decimal = Decimal('100000'),
                 high_value_threshold: Decimal = Decimal('10000')):
        """
        Initialize TransactionRulesService with configurable limits
        
        Args:
            withdrawal_daily_limit: Maximum daily withdrawal limit
            transfer_daily_limit: Maximum daily transfer limit
            high_value_threshold: Threshold for high-value transactions requiring additional verification
        """
        self._withdrawal_daily_limit = withdrawal_daily_limit
        self._transfer_daily_limit = transfer_daily_limit
        self._high_value_threshold = high_value_threshold
    
    def validate_transaction(self, transaction: Transaction) -> List[str]:
        """
        Validate a transaction against business rules
        
        Args:
            transaction: Transaction to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Basic validation
        if transaction.amount <= Decimal('0'):
            errors.append("Transaction amount must be positive")
        
        if transaction.transaction_type is None:
            errors.append("Transaction type is required")
        
        if transaction.account_id is None:
            errors.append("Account ID is required")
        
        # Transaction type specific validation
        if transaction.transaction_type == TransactionType.TRANSFER:
            if transaction.to_account_id is None:
                errors.append("Target account ID is required for transfers")
            
            if transaction.account_id == transaction.to_account_id:
                errors.append("Cannot transfer to the same account")
            
            # Check transfer limits
            if transaction.amount > self._transfer_daily_limit:
                errors.append(f"Transfer amount exceeds daily limit of {self._transfer_daily_limit}")
        
        elif transaction.transaction_type == TransactionType.WITHDRAWAL:
            # Check withdrawal limits
            if transaction.amount > self._withdrawal_daily_limit:
                errors.append(f"Withdrawal amount exceeds daily limit of {self._withdrawal_daily_limit}")
        
        return errors
    
    def requires_additional_verification(self, transaction: Transaction) -> bool:
        """
        Check if transaction requires additional verification
        
        Args:
            transaction: Transaction to check
            
        Returns:
            True if additional verification is required
        """
        # High-value transactions require additional verification
        if transaction.amount >= self._high_value_threshold:
            return True
        
        # International transfers require additional verification
        if (transaction.transaction_type == TransactionType.TRANSFER and 
            transaction.metadata and 
            transaction.metadata.tags.get('international') == 'true'):
            return True
        
        # Suspicious activity flag requires additional verification
        if transaction.metadata and transaction.metadata.tags.get('suspicious') == 'true':
            return True
        
        return False
    
    def get_transaction_fee(self, transaction: Transaction) -> Decimal:
        """
        Calculate applicable transaction fee
        
        Args:
            transaction: Transaction to calculate fee for
            
        Returns:
            Fee amount
        """
        if transaction.transaction_type == TransactionType.DEPOSIT:
            return Decimal('0')  # No fee for deposits
        
        elif transaction.transaction_type == TransactionType.WITHDRAWAL:
            # Basic fee structure for withdrawals
            if transaction.amount < Decimal('1000'):
                return Decimal('0')  # No fee for small withdrawals
            elif transaction.amount < Decimal('10000'):
                return Decimal('25')  # Fixed fee for medium withdrawals
            else:
                return transaction.amount * Decimal('0.003')  # 0.3% for large withdrawals
        
        elif transaction.transaction_type == TransactionType.TRANSFER:
            # Check if it's an internal transfer
            is_internal = transaction.metadata and transaction.metadata.tags.get('internal') == 'true'
            
            if is_internal:
                return Decimal('0')  # No fee for internal transfers
            else:
                # External transfer fee
                return transaction.amount * Decimal('0.002')  # 0.2% for external transfers
        
        return Decimal('0')  # Default: no fee
