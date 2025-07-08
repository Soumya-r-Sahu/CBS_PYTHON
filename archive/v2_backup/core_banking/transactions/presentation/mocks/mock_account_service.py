"""
Mock Account Service

Mock implementation of account service for testing and development.
"""
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID

from ...application.interfaces.account_service_interface import AccountServiceInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path


class MockAccountService(AccountServiceInterface):
    """Mock implementation of account service for testing"""
    
    def __init__(self):
        """Initialize with mock data"""
        self._accounts = {
            "1234567890": {
                "id": "acc-1234",
                "account_number": "1234567890",
                "customer_id": "cust-1234",
                "customer_name": "John Doe",
                "balance": Decimal("1000.00"),
                "status": "active",
                "type": "savings"
            },
            "0987654321": {
                "id": "acc-5678",
                "account_number": "0987654321",
                "customer_id": "cust-5678",
                "customer_name": "Jane Smith",
                "balance": Decimal("5000.00"),
                "status": "active",
                "type": "checking"
            },
            "5432167890": {
                "id": "acc-9012",
                "account_number": "5432167890",
                "customer_id": "cust-9012",
                "customer_name": "Alice Johnson",
                "balance": Decimal("0.00"),
                "status": "blocked",
                "type": "savings"
            }
        }
    
    def get_account(self, account_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get account data by ID or account number
        
        Args:
            account_id: Account ID or account number
            
        Returns:
            Account data if found, None otherwise
        """
        account_str = str(account_id)
        
        # Check if it's a direct match
        if account_str in self._accounts:
            return self._accounts[account_str]
        
        # Look up by account number
        for account in self._accounts.values():
            if account.get("id") == account_str:
                return account
        
        return None
    
    def update_balance(self, account_id: UUID, amount: Decimal, is_credit: bool) -> Optional[Dict[str, Any]]:
        """
        Update account balance
        
        Args:
            account_id: Account ID to update
            amount: Amount to add or subtract
            is_credit: True for credit (increase balance), False for debit (decrease balance)
            
        Returns:
            Updated account data if successful, None otherwise
        """
        account = self.get_account(account_id)
        if not account:
            return None
        
        # Check account status
        if account["status"] != "active":
            return None
        
        # Check funds for debit
        if not is_credit and account["balance"] < amount:
            return None
        
        # Update balance
        if is_credit:
            account["balance"] += amount
        else:
            account["balance"] -= amount
        
        return account
    
    def validate_account_status(self, account_id: UUID) -> Dict[str, Any]:
        """
        Validate if an account is active and can perform transactions
        
        Args:
            account_id: Account ID to validate
            
        Returns:
            Dictionary with validation results
        """
        account = self.get_account(account_id)
        
        if not account:
            return {
                "is_valid": False,
                "can_debit": False,
                "can_credit": False,
                "errors": ["Account not found"]
            }
        
        if account["status"] != "active":
            return {
                "is_valid": False,
                "can_debit": False,
                "can_credit": False,
                "errors": [f"Account is {account['status']}"]
            }
        
        return {
            "is_valid": True,
            "can_debit": True,
            "can_credit": True,
            "errors": []
        }
    
    def check_balance(self, account_id: UUID, required_amount: Decimal) -> Dict[str, Any]:
        """
        Check if account has sufficient balance
        
        Args:
            account_id: Account ID to check
            required_amount: Amount required
            
        Returns:
            Dictionary with check results
        """
        account = self.get_account(account_id)
        
        if not account:
            return {
                "has_funds": False,
                "current_balance": Decimal("0.00"),
                "available_balance": Decimal("0.00")
            }
        
        current_balance = account["balance"]
        available_balance = current_balance  # In a real implementation, might consider pending transactions
        
        return {
            "has_funds": available_balance >= required_amount,
            "current_balance": current_balance,
            "available_balance": available_balance
        }
