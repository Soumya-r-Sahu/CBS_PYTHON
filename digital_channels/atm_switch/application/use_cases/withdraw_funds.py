"""
Withdraw Funds Use Case

This module implements the withdraw funds use case for the ATM module.
"""

from decimal import Decimal
from typing import Dict, Any, Optional

from ..interfaces import AtmRepositoryInterface, NotificationServiceInterface
from ...domain.entities import Transaction
from ...domain.validators import TransactionValidator
from ...domain.services import TransactionRules


class WithdrawFundsUseCase:
    """Use case for withdrawing funds from an ATM"""
    
    def __init__(
        self, 
        repository: AtmRepositoryInterface,
        notification_service: NotificationServiceInterface,
        withdrawal_fee: Decimal = Decimal('0'),
        daily_withdrawal_limit: Decimal = Decimal('25000'),
        min_withdrawal: Decimal = Decimal('100'),
        max_withdrawal: Decimal = Decimal('10000')
    ):
        """
        Initialize withdraw funds use case
        
        Args:
            repository: ATM repository
            notification_service: Notification service
            withdrawal_fee: Fee for withdrawals
            daily_withdrawal_limit: Daily withdrawal limit
            min_withdrawal: Minimum withdrawal amount
            max_withdrawal: Maximum withdrawal amount
        """
        self.repository = repository
        self.notification_service = notification_service
        self.withdrawal_fee = withdrawal_fee
        self.daily_withdrawal_limit = daily_withdrawal_limit
        self.min_withdrawal = min_withdrawal
        self.max_withdrawal = max_withdrawal
    
    def execute(self, session_token: str, amount: Decimal) -> Dict[str, Any]:
        """
        Execute withdraw funds use case
        
        Args:
            session_token: ATM session token
            amount: Amount to withdraw
            
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
        
        # Validate amount
        amount_validation = TransactionValidator.validate_withdrawal_amount(
            amount, self.min_withdrawal, self.max_withdrawal
        )
        
        if not amount_validation['valid']:
            return {
                'success': False,
                'message': amount_validation['message']
            }
        
        # Validate denomination
        denomination_validation = TransactionValidator.validate_denomination(amount)
        
        if not denomination_validation['valid']:
            return {
                'success': False,
                'message': denomination_validation['message']
            }
        
        # Get account
        account = self.repository.get_account_by_id(session.account_id)
        
        if not account:
            return {
                'success': False,
                'message': 'Account not found'
            }
        
        # Check daily withdrawal limit
        todays_withdrawals = self.repository.get_today_withdrawals(account.account_id)
        
        daily_limit_validation = TransactionValidator.validate_daily_limit(
            amount, todays_withdrawals, self.daily_withdrawal_limit
        )
        
        if not daily_limit_validation['valid']:
            return {
                'success': False,
                'message': daily_limit_validation['message']
            }
        
        # Execute withdrawal
        withdrawal_result = TransactionRules.execute_withdrawal(
            account, amount, self.withdrawal_fee
        )
        
        if not withdrawal_result['success']:
            return {
                'success': False,
                'message': withdrawal_result['message']
            }
        
        # Update account balance
        if not self.repository.update_account_balance(account):
            return {
                'success': False,
                'message': 'Failed to update account balance'
            }
        
        # Create withdrawal transaction
        withdrawal_transaction = Transaction(
            amount=-amount,  # Negative for debit
            account_id=account.account_id,
            transaction_type="ATM_WITHDRAWAL",
            description="ATM Cash Withdrawal",
            balance_before=withdrawal_result['balance_before'],
            balance_after=withdrawal_result['balance_after']
        )
        
        if not self.repository.create_transaction(withdrawal_transaction):
            # This is a critical error - the account balance was updated but no transaction record created
            return {
                'success': False,
                'message': 'Failed to record transaction'
            }
        
        # Create fee transaction if applicable
        if self.withdrawal_fee > Decimal('0'):
            fee_transaction = Transaction(
                amount=-self.withdrawal_fee,  # Negative for debit
                account_id=account.account_id,
                transaction_type="ATM_FEE",
                description="ATM Withdrawal Fee",
                balance_before=withdrawal_result['balance_before'] - amount,
                balance_after=withdrawal_result['balance_after']
            )
            
            self.repository.create_transaction(fee_transaction)
        
        # Send notification
        self.notification_service.send_withdrawal_notification(
            account_number=account.account_number,
            amount=amount,
            transaction_id=withdrawal_transaction.transaction_id,
            balance=account.balance
        )
        
        # Return success result
        return {
            'success': True,
            'transaction_id': withdrawal_transaction.transaction_id,
            'amount': str(amount),
            'fee': str(self.withdrawal_fee) if self.withdrawal_fee > Decimal('0') else '0',
            'total': str(amount + self.withdrawal_fee),
            'balance': str(account.balance),
            'datetime': withdrawal_transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
