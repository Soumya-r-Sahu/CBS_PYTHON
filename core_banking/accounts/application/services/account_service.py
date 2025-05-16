"""
Account Service

This module provides application services for account management.
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import date
from uuid import UUID

from ..use_cases.create_account import CreateAccountUseCase
from ..use_cases.deposit_funds import DepositFundsUseCase
from ..use_cases.withdraw_funds import WithdrawFundsUseCase
from ..use_cases.transfer_funds import TransferFundsUseCase
from ..use_cases.get_account_details import GetAccountDetailsUseCase
from ..use_cases.close_account import CloseAccountUseCase
from ..use_cases.get_account_statement import GetAccountStatementUseCase
# Import other use cases as needed


class AccountService:
    """
    Application service for account management
    
    This service orchestrates multiple use cases to provide a unified interface
    for account operations.
    """
    
    def __init__(
        self,
        create_account_use_case: CreateAccountUseCase,
        deposit_funds_use_case: DepositFundsUseCase,
        withdraw_funds_use_case: WithdrawFundsUseCase,
        transfer_funds_use_case: TransferFundsUseCase,
        get_account_details_use_case: GetAccountDetailsUseCase,
        close_account_use_case: CloseAccountUseCase,
        get_account_statement_use_case: GetAccountStatementUseCase
    ):
        """
        Initialize account service
        
        Args:
            create_account_use_case: Create account use case
            deposit_funds_use_case: Deposit funds use case
            withdraw_funds_use_case: Withdraw funds use case
            transfer_funds_use_case: Transfer funds use case
            get_account_details_use_case: Get account details use case
            close_account_use_case: Close account use case
            get_account_statement_use_case: Get account statement use case
        """
        self.create_account_use_case = create_account_use_case
        self.deposit_funds_use_case = deposit_funds_use_case
        self.withdraw_funds_use_case = withdraw_funds_use_case
        self.transfer_funds_use_case = transfer_funds_use_case
        self.get_account_details_use_case = get_account_details_use_case
        self.close_account_use_case = close_account_use_case
        self.get_account_statement_use_case = get_account_statement_use_case
    
    def create_account(
        self,
        customer_id: UUID,
        account_type: str,
        initial_deposit: Optional[Decimal] = None,
        currency: str = "INR"
    ) -> Dict[str, Any]:
        """
        Create a new account
        
        Args:
            customer_id: ID of the customer who owns the account
            account_type: Type of account to create (SAVINGS, CURRENT, etc.)
            initial_deposit: Optional initial deposit amount
            currency: Currency code (default: INR)
            
        Returns:
            Result dictionary with account details
        """
        return self.create_account_use_case.execute(
            customer_id=customer_id,
            account_type=account_type,
            initial_deposit=initial_deposit,
            currency=currency
        )
    
    def deposit(
        self,
        account_id: UUID,
        amount: Decimal,
        description: Optional[str] = None,
        reference_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deposit funds into an account
        
        Args:
            account_id: ID of the account to deposit to
            amount: Amount to deposit
            description: Optional transaction description
            reference_id: Optional external reference ID
            
        Returns:
            Result dictionary with transaction details
        """
        return self.deposit_funds_use_case.execute(
            account_id=account_id,
            amount=amount,
            description=description,
            reference_id=reference_id
        )
    
    def withdraw(
        self,
        account_id: UUID,
        amount: Decimal,
        description: Optional[str] = None,
        reference_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Withdraw funds from an account
        
        Args:
            account_id: ID of the account to withdraw from
            amount: Amount to withdraw
            description: Optional transaction description
            reference_id: Optional external reference ID
            
        Returns:
            Result dictionary with transaction details
        """
        return self.withdraw_funds_use_case.execute(
            account_id=account_id,
            amount=amount,
            description=description,
            reference_id=reference_id
        )
    
    def transfer(
        self,
        source_account_id: UUID,
        target_account_id: UUID,
        amount: Decimal,
        description: Optional[str] = None,
        reference_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transfer funds between accounts
        
        Args:
            source_account_id: ID of the source account
            target_account_id: ID of the target account
            amount: Amount to transfer
            description: Optional transaction description
            reference_id: Optional external reference ID
        
        Returns:
            Result dictionary with transaction details
        """
        return self.transfer_funds_use_case.execute(
            source_account_id=source_account_id,
            target_account_id=target_account_id,
            amount=amount,
            description=description,
            reference_id=reference_id
        )

    def get_account_details(self, account_id: UUID) -> Dict[str, Any]:
        """
        Get account details
        
        Args:
            account_id: ID of the account to get details for
        
        Returns:
            Result dictionary with account details
        """
        return self.get_account_details_use_case.execute(account_id=account_id)

    def close_account(
        self,
        account_id: UUID,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Close an account
        
        Args:
            account_id: ID of the account to close
            reason: Optional reason for closing the account
        
        Returns:
            Result dictionary with account details
        """
        return self.close_account_use_case.execute(
            account_id=account_id,
            reason=reason
        )
