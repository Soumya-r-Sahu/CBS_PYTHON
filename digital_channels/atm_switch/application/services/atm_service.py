"""
ATM Service

This module provides application services for ATM operations, orchestrating use cases.
"""

from typing import Dict, Any, Optional
from decimal import Decimal

from ..interfaces import AtmRepository, NotificationServiceInterface
from ..use_cases.withdraw_cash import WithdrawCashUseCase
from ..use_cases.check_balance import CheckBalanceUseCase
from ..use_cases.change_pin import ChangePinUseCase
from ..use_cases.get_mini_statement import GetMiniStatementUseCase
from ..use_cases.validate_card import ValidateCardUseCase


class AtmService:
    """
    Application service for ATM operations
    
    This service orchestrates multiple use cases to provide a unified interface for ATM operations.
    """
    
    def __init__(
        self,
        withdraw_cash: WithdrawCashUseCase,
        check_balance: CheckBalanceUseCase,
        change_pin: ChangePinUseCase,
        get_mini_statement: GetMiniStatementUseCase,
        validate_card: ValidateCardUseCase
    ):
        """
        Initialize ATM service
        
        Args:
            withdraw_cash: Withdraw cash use case
            check_balance: Check balance use case
            change_pin: Change PIN use case
            get_mini_statement: Get mini statement use case
            validate_card: Validate card use case
        """
        self.withdraw_cash = withdraw_cash
        self.check_balance = check_balance
        self.change_pin = change_pin
        self.get_mini_statement = get_mini_statement
        self.validate_card = validate_card
        
    def login(self, card_number: str, pin: str) -> Dict[str, Any]:
        """
        Validate card and create a session
        
        Args:
            card_number: Card number
            pin: PIN
            
        Returns:
            Result dictionary with session token and status
        """
        return self.validate_card.execute(card_number, pin)
        
    def withdraw(self, session_token: str, amount: Decimal) -> Dict[str, Any]:
        """
        Withdraw cash
        
        Args:
            session_token: Session token
            amount: Amount to withdraw
            
        Returns:
            Result dictionary with status and transaction details
        """
        return self.withdraw_cash.execute(session_token, amount)
        
    def get_balance(self, session_token: str) -> Dict[str, Any]:
        """
        Get account balance
        
        Args:
            session_token: Session token
            
        Returns:
            Result dictionary with balance information
        """
        return self.check_balance.execute(session_token)
        
    def update_pin(self, session_token: str, old_pin: str, new_pin: str) -> Dict[str, Any]:
        """
        Change card PIN
        
        Args:
            session_token: Session token
            old_pin: Current PIN
            new_pin: New PIN
            
        Returns:
            Result dictionary with status
        """
        return self.change_pin.execute(session_token, old_pin, new_pin)
        
    def get_statement(self, session_token: str, count: int = 10) -> Dict[str, Any]:
        """
        Get mini statement
        
        Args:
            session_token: Session token
            count: Maximum number of transactions
            
        Returns:
            Result dictionary with transaction list
        """
        return self.get_mini_statement.execute(session_token, count)
