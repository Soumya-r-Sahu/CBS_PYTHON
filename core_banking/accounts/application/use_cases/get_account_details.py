"""
Get Account Details Use Case

This module implements the use case for retrieving account details.
"""

from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID

from ..interfaces.account_repository import AccountRepositoryInterface


class GetAccountDetailsUseCase:
    """Use case for retrieving account details"""
    
    def __init__(self, account_repository: AccountRepositoryInterface):
        self.account_repository = account_repository
    
    def execute(self, account_identifier: str, id_type: str = "number") -> Dict[str, Any]:
        """
        Execute the get account details use case
        
        Args:
            account_identifier: Account ID or number
            id_type: Type of identifier ('id' or 'number')
            
        Returns:
            Dictionary with account details
        """
        account = None
        
        if id_type == "id":
            try:
                account_id = UUID(account_identifier)
                account = self.account_repository.get_by_id(account_id)
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid account ID format",
                    "errors": ["Invalid account ID format"]
                }
        elif id_type == "number":
            account = self.account_repository.get_by_account_number(account_identifier)
        else:
            return {
                "success": False,
                "message": "Invalid ID type",
                "errors": ["ID type must be 'id' or 'number'"]
            }
        
        if not account:
            return {
                "success": False,
                "message": "Account not found",
                "errors": ["Account not found"]
            }
        
        return {
            "success": True,
            "message": "Account details retrieved successfully",
            "data": {
                "id": str(account.id),
                "account_number": account.account_number,
                "customer_id": str(account.customer_id),
                "account_type": account.account_type.value,
                "balance": str(account.balance),
                "status": account.status.value,
                "currency": account.currency,
                "created_at": account.created_at.isoformat(),
                "updated_at": account.updated_at.isoformat(),
                "interest_rate": str(account.interest_rate) if account.interest_rate is not None else None,
                "overdraft_limit": str(account.overdraft_limit) if account.overdraft_limit is not None else None
            }
        }
