"""
Get Account Statement Use Case

This module defines the use case for retrieving an account statement.
"""

from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta

from ..interfaces.account_repository import AccountRepository
from ..interfaces.transaction_repository import TransactionRepository

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class GetAccountStatementUseCase:
    """
    Use case for retrieving an account statement
    
    This use case retrieves a list of transactions for an account within a specified date range,
    along with account details and summary information.
    """
    
    def __init__(
        self,
        account_repository: AccountRepository,
        transaction_repository: TransactionRepository
    ):
        """
        Initialize the use case
        
        Args:
            account_repository: Repository for account data access
            transaction_repository: Repository for transaction data access
        """
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository
    
    def execute(
        self,
        account_id: UUID,
        start_date: datetime = None,
        end_date: datetime = None,
        transaction_type: str = None,
        limit: int = None,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Execute the get account statement use case
        
        Args:
            account_id: ID of the account to get statement for
            start_date: Optional starting date for the statement period
            end_date: Optional ending date for the statement period
            transaction_type: Optional transaction type filter
            limit: Optional limit on the number of transactions to return
            offset: Optional offset for pagination
            
        Returns:
            Result dictionary with account statement details
            
        Raises:
            ValueError: If the account does not exist
        """
        # Default date range if not provided (last 30 days)
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # Get the account
        account = self.account_repository.get_by_id(account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
        
        # Get transactions for the account within the date range
        transactions = self.transaction_repository.get_by_account_id_and_date_range(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type,
            limit=limit,
            offset=offset
        )
        
        # Calculate summary information
        opening_balance = self._calculate_opening_balance(account_id, start_date)
        closing_balance = account.balance.value
        
        total_credits = sum(
            tx.amount.value 
            for tx in transactions 
            if tx.transaction_type in ["DEPOSIT", "TRANSFER_IN"]
        )
        
        total_debits = sum(
            tx.amount.value 
            for tx in transactions 
            if tx.transaction_type in ["WITHDRAWAL", "TRANSFER_OUT", "FEE"]
        )
        
        # Return the statement
        return {
            "success": True,
            "account_id": str(account_id),
            "account_number": account.account_number,
            "account_type": account.account_type.value,
            "currency": account.currency,
            "statement_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "opening_balance": str(opening_balance),
            "closing_balance": str(closing_balance),
            "total_credits": str(total_credits),
            "total_debits": str(total_debits),
            "transactions": [
                {
                    "transaction_id": str(tx.transaction_id),
                    "date": tx.timestamp.isoformat(),
                    "description": tx.description,
                    "reference_id": tx.reference_id,
                    "amount": str(tx.amount.value),
                    "type": tx.transaction_type.value,
                    "status": tx.status.value,
                    "running_balance": str(tx.resulting_balance.value) if tx.resulting_balance else None
                }
                for tx in transactions
            ],
            "total_records": len(transactions)
        }
    
    def _calculate_opening_balance(self, account_id: UUID, start_date: datetime) -> float:
        """
        Calculate opening balance for the statement period
        
        Args:
            account_id: ID of the account
            start_date: Start date for the statement period
            
        Returns:
            Opening balance amount
        """
        # Get the latest transaction before the start date
        latest_tx_before_start = self.transaction_repository.get_latest_before_date(
            account_id=account_id, 
            date=start_date
        )
        
        if latest_tx_before_start and latest_tx_before_start.resulting_balance:
            return latest_tx_before_start.resulting_balance.value
        else:
            # If no transactions before start date, get account creation details
            account = self.account_repository.get_by_id(account_id)
            
            # In a real system, we would have more detailed historical data
            # Here we're simplifying and returning the current balance
            return account.balance.value
