"""
Transaction Rules Service

This module defines transaction business rules for the ATM domain.
"""

from decimal import Decimal
from typing import Dict, Any, List
from datetime import datetime, time

from ..entities.account import Account

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class TransactionRules:
    """Core business rules for ATM transactions"""
    
    @staticmethod
    def check_transaction_limits(
        amount: Decimal,
        account_type: str,
        daily_total: Decimal
    ) -> Dict[str, Any]:
        """
        Check transaction against account type limits
        
        Args:
            amount: Transaction amount
            account_type: Type of account (SAVINGS, CURRENT, etc.)
            daily_total: Total transactions for the day so far
            
        Returns:
            Dictionary with validation result
        """
        # Define limits based on account type
        limits = {
            'SAVINGS': {
                'per_transaction': Decimal('25000'),
                'daily': Decimal('100000')
            },
            'CURRENT': {
                'per_transaction': Decimal('50000'),
                'daily': Decimal('200000')
            },
            'PREMIUM': {
                'per_transaction': Decimal('100000'),
                'daily': Decimal('500000')
            }
        }
        
        # Use default limits if account type not found
        account_limits = limits.get(account_type, limits['SAVINGS'])
        
        # Check per-transaction limit
        if amount > account_limits['per_transaction']:
            return {
                'valid': False,
                'message': f'Transaction amount exceeds the {account_type} account limit of {account_limits["per_transaction"]}'
            }
        
        # Check daily limit
        if daily_total + amount > account_limits['daily']:
            return {
                'valid': False,
                'message': f'Transaction would exceed daily limit of {account_limits["daily"]}'
            }
        
        return {'valid': True}
    
    @staticmethod
    def check_business_hours(transaction_type: str) -> Dict[str, Any]:
        """
        Check if transaction is allowed during current hours
        
        Args:
            transaction_type: Type of transaction
            
        Returns:
            Dictionary with validation result
        """
        current_time = datetime.now().time()
        current_day = datetime.now().weekday()  # 0-6, Monday is 0
        
        # Transactions restricted during maintenance hours
        # Typically between 00:00 and 01:00
        maintenance_start = time(0, 0)
        maintenance_end = time(1, 0)
        
        # Check if we're in maintenance hours
        if maintenance_start <= current_time <= maintenance_end:
            return {
                'valid': False,
                'message': 'System maintenance in progress. Please try again later.'
            }
        
        # High-value transactions only during banking hours on weekdays
        banking_hours = {
            'start': time(9, 0),
            'end': time(18, 0)
        }
        
        high_value_types = ['LARGE_WITHDRAWAL', 'LARGE_TRANSFER']
        
        if (transaction_type in high_value_types and 
                (current_day >= 5 or  # Weekend
                 not (banking_hours['start'] <= current_time <= banking_hours['end']))):
            return {
                'valid': False,
                'message': 'High-value transactions are only allowed during banking hours (9:00-18:00) on weekdays.'
            }
        
        return {'valid': True}
    
    @staticmethod
    def apply_transaction_fees(
        transaction_type: str,
        amount: Decimal,
        account_type: str,
        monthly_transaction_count: int
    ) -> Decimal:
        """
        Calculate applicable transaction fees
        
        Args:
            transaction_type: Type of transaction
            amount: Transaction amount
            account_type: Type of account
            monthly_transaction_count: Number of transactions in current month
            
        Returns:
            Fee amount
        """
        # Define fee structure
        fee_structure = {
            'WITHDRAWAL': {
                'SAVINGS': {
                    'base_fee': Decimal('0'),  # Free withdrawals up to a limit
                    'free_transactions': 5,  # 5 free withdrawals per month
                    'additional_fee': Decimal('20')  # Fee for additional withdrawals
                },
                'CURRENT': {
                    'base_fee': Decimal('0'),
                    'free_transactions': 10,
                    'additional_fee': Decimal('10')
                },
                'PREMIUM': {
                    'base_fee': Decimal('0'),
                    'free_transactions': 999,  # Unlimited free withdrawals
                    'additional_fee': Decimal('0')
                }
            },
            'TRANSFER': {
                'SAVINGS': {
                    'base_fee': Decimal('5'),
                    'free_transactions': 3,
                    'additional_fee': Decimal('15')
                },
                'CURRENT': {
                    'base_fee': Decimal('3'),
                    'free_transactions': 5,
                    'additional_fee': Decimal('10')
                },
                'PREMIUM': {
                    'base_fee': Decimal('0'),
                    'free_transactions': 999,
                    'additional_fee': Decimal('0')
                }
            }
        }
        
        # Get fee details for transaction and account type
        try:
            fee_details = fee_structure[transaction_type][account_type]
        except KeyError:
            # If combination not found, use default fee
            return Decimal('0')
        
        # Calculate fee based on monthly transaction count
        if monthly_transaction_count <= fee_details['free_transactions']:
            return fee_details['base_fee']
        else:
            return fee_details['base_fee'] + fee_details['additional_fee']
    
    @staticmethod
    def can_withdraw(
        account: Account, 
        amount: Decimal,
        fee: Decimal = Decimal('0')
    ) -> Dict[str, Any]:
        """
        Determine if withdrawal is allowed based on account status and balance
        
        Args:
            account: The account to check
            amount: Amount to withdraw
            fee: Transaction fee if applicable
            
        Returns:
            Dictionary with result and message
        """
        if not account.is_active():
            return {
                'allowed': False,
                'message': f'Account is {account.status.lower()}'
            }
        
        total_debit = amount + fee
        
        if not account.has_sufficient_balance(total_debit):
            return {
                'allowed': False,
                'message': 'Insufficient funds'
            }
        
        return {
            'allowed': True,
            'message': 'Withdrawal allowed'
        }
    
    @staticmethod
    def execute_withdrawal(
        account: Account,
        amount: Decimal,
        fee: Decimal = Decimal('0')
    ) -> Dict[str, Any]:
        """
        Execute withdrawal from account
        
        Args:
            account: The account to debit
            amount: Amount to withdraw
            fee: Transaction fee if applicable
            
        Returns:
            Dictionary with transaction result
        """
        total_debit = amount + fee
        check_result = TransactionRules.can_withdraw(account, amount, fee)
        
        if not check_result['allowed']:
            return {
                'success': False,
                'message': check_result['message']
            }
        
        # Record balance before transaction
        balance_before = account.balance
        
        # Debit account
        if not account.debit(total_debit):
            return {
                'success': False,
                'message': 'Failed to debit account'
            }
        
        return {
            'success': True,
            'balance_before': balance_before,
            'balance_after': account.balance,
            'total_debit': total_debit
        }
    
    @staticmethod
    def execute_deposit(
        account: Account,
        amount: Decimal
    ) -> Dict[str, Any]:
        """
        Execute deposit to account
        
        Args:
            account: The account to credit
            amount: Amount to deposit
            
        Returns:
            Dictionary with transaction result
        """
        if not account.is_active():
            return {
                'success': False,
                'message': f'Account is {account.status.lower()}'
            }
        
        if amount <= Decimal('0'):
            return {
                'success': False,
                'message': 'Deposit amount must be greater than zero'
            }
        
        # Record balance before transaction
        balance_before = account.balance
        
        # Credit account
        if not account.credit(amount):
            return {
                'success': False,
                'message': 'Failed to credit account'
            }
        
        return {
            'success': True,
            'balance_before': balance_before,
            'balance_after': account.balance,
            'amount': amount
        }
