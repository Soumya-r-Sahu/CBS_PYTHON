"""
Withdraw Cash Use Case

This module defines the use case for withdrawing cash from an ATM.
"""

from decimal import Decimal
from typing import Dict, Any
from datetime import datetime

from ....domain.entities.transaction import Transaction
from ....domain.validators.transaction_validator import TransactionValidator
from ....domain.services.transaction_rules import TransactionRules
from ..interfaces import AtmRepository, NotificationServiceInterface


class WithdrawCashUseCase:
    """Use case for withdrawing cash from an ATM"""
    
    def __init__(
        self, 
        atm_repository: AtmRepository,
        notification_service: NotificationServiceInterface,
        withdrawal_fee: Decimal = Decimal('0'),
        daily_withdrawal_limit: Decimal = Decimal('25000'),
        min_withdrawal: Decimal = Decimal('100'),
        max_withdrawal: Decimal = Decimal('10000')
    ):
        self.atm_repository = atm_repository
        self.notification_service = notification_service
        self.withdrawal_fee = withdrawal_fee
        self.daily_withdrawal_limit = daily_withdrawal_limit
        self.min_withdrawal = min_withdrawal
        self.max_withdrawal = max_withdrawal
    
    def execute(self, session_token: str, amount: Decimal) -> Dict[str, Any]:
        """
        Execute the withdraw cash use case
        
        Args:
            session_token: ATM session token
            amount: Amount to withdraw
            
        Returns:
            Result dictionary with success flag and additional information
        """
        # Input validation
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
        
        # Get session
        session = self.atm_repository.get_session_by_token(session_token)
        if not session:
            return {
                'success': False,
                'message': 'Invalid session'
            }
        
        if not session.is_valid():
            return {
                'success': False,
                'message': 'Session expired'
            }
        
        # Get account
        account = self.atm_repository.get_account_by_id(session.account_id)
        if not account:
            return {
                'success': False,
                'message': 'Account not found'
            }
        
        # Get card
        card = self.atm_repository.get_card_by_number(session.card_number)
        if not card:
            return {
                'success': False,
                'message': 'Card not found'
            }
        
        if not card.is_valid():
            return {
                'success': False,
                'message': 'Card is not valid'
            }
        
        # Check daily withdrawal limit
        todays_withdrawals = self.atm_repository.get_today_withdrawals(account.account_id)
        daily_limit_validation = TransactionValidator.validate_daily_limit(
            amount, todays_withdrawals, self.daily_withdrawal_limit
        )
        if not daily_limit_validation['valid']:
            return {
                'success': False,
                'message': daily_limit_validation['message']
            }
        
        # Check transaction limits based on account type
        limit_check = TransactionRules.check_transaction_limits(
            amount, account.account_type, todays_withdrawals
        )
        if not limit_check['valid']:
            return {
                'success': False,
                'message': limit_check['message']
            }
        
        # Check business hours for high-value transactions
        if amount >= Decimal('10000'):
            hour_check = TransactionRules.check_business_hours('LARGE_WITHDRAWAL')
            if not hour_check['valid']:
                return {
                    'success': False,
                    'message': hour_check['message']
                }
        
        # Calculate fee
        monthly_withdrawals = self.atm_repository.get_monthly_withdrawals_count(account.account_id)
        fee = TransactionRules.apply_transaction_fees(
            'WITHDRAWAL', amount, account.account_type, monthly_withdrawals
        )
        
        # Calculate total debit including fee
        total_debit = amount + fee
        
        # Check sufficient balance
        withdrawal_check = TransactionRules.can_withdraw(account, amount, fee)
        if not withdrawal_check['allowed']:
            return {
                'success': False,
                'message': withdrawal_check['message']
            }
        
        # Execute withdrawal
        withdrawal_result = TransactionRules.execute_withdrawal(account, amount, fee)
        if not withdrawal_result['success']:
            return {
                'success': False,
                'message': withdrawal_result['message']
            }
        
        # Create withdrawal transaction
        transaction = Transaction(
            transaction_id=None,  # Will be generated
            amount=amount,
            account_id=account.account_id,
            transaction_type="ATM_WITHDRAWAL",
            description="ATM Cash Withdrawal",
            fee=fee
        )
        
        # Complete transaction
        transaction.complete(
            withdrawal_result['balance_before'], 
            withdrawal_result['balance_after']
        )
        
        # Save transaction and update account in repository
        self.atm_repository.save_transaction(transaction)
        self.atm_repository.update_account_balance(
            account.account_id, 
            account.balance
        )
        
        # Record card usage
        card.record_usage()
        self.atm_repository.update_card(card)
        
        # Send notification
        self.notification_service.send_withdrawal_notification(
            account.account_number,
            amount,
            transaction.transaction_id,
            account.balance
        )
        
        # Return success response
        return {
            'success': True,
            'transaction_id': transaction.transaction_id,
            'amount': str(amount),
            'fee': str(fee),
            'total': str(total_debit),
            'balance': str(account.balance),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
