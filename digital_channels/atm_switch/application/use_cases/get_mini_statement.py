"""
Get Mini Statement Use Case

This module implements the get mini statement use case for the ATM module.
"""

from typing import Dict, Any, List
from datetime import datetime

from ..interfaces import AtmRepository


class GetMiniStatementUseCase:
    """Use case for getting mini statement via ATM"""
    
    def __init__(
        self, 
        repository: AtmRepository,
        max_transactions: int = 10
    ):
        """
        Initialize get mini statement use case
        
        Args:
            repository: ATM repository
            max_transactions: Maximum number of transactions to include
        """
        self.repository = repository
        self.max_transactions = max_transactions
    
    def execute(self, session_token: str) -> Dict[str, Any]:
        """
        Execute get mini statement use case
        
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
        
        # Create mini statement transaction
        transaction = self.repository.create_transaction({
            'amount': 0,  # Zero amount for mini statement
            'account_id': account.account_id,
            'transaction_type': 'ATM_MINI_STATEMENT',
            'description': 'ATM Mini Statement',
            'balance_before': account.balance,
            'balance_after': account.balance
        })
        
        # Get recent transactions
        transactions = self.repository.get_transactions_by_account(
            account.account_id, 
            self.max_transactions
        )
        
        # Format transactions for mini statement
        transactions_list = []
        for t in transactions:
            transactions_list.append({
                'date': t.timestamp.strftime('%d-%m-%Y'),
                'description': t.description,
                'amount': str(t.amount),
                'type': 'CR' if t.amount > 0 else 'DR',
                'balance': str(t.balance_after)
            })
        
        # Return success result
        return {
            'success': True,
            'account_number': account.account_number,
            'transactions': transactions_list,
            'current_balance': str(account.balance),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
