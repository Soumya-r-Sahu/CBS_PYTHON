"""
Create Account Use Case

This module implements the use case for creating a bank account.
"""

from decimal import Decimal
from typing import Dict, Any
from uuid import UUID

from ...domain.entities.account import Account, AccountType, AccountStatus
from ...domain.validators.account_validator import AccountValidator
from ...domain.value_objects.money import Money
from ..interfaces.account_repository import AccountRepositoryInterface
from ..interfaces.notification_service import NotificationServiceInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class CreateAccountUseCase:
    """Use case for creating a bank account"""
    
    def __init__(
        self,
        account_repository: AccountRepositoryInterface,
        notification_service: NotificationServiceInterface
    ):
        self.account_repository = account_repository
        self.notification_service = notification_service
    
    def execute(
        self,
        account_number: str,
        customer_id: str,
        account_type: str,
        currency: str = "INR",
        initial_deposit: Decimal = Decimal('0.00'),
        interest_rate: Decimal = None,
        overdraft_limit: Decimal = None
    ) -> Dict[str, Any]:
        """
        Execute the create account use case
        
        Args:
            account_number: The account number
            customer_id: The customer ID
            account_type: The type of account
            currency: The account currency
            initial_deposit: Initial deposit amount
            interest_rate: Interest rate for the account
            overdraft_limit: Overdraft limit for current accounts
            
        Returns:
            Dictionary with creation result
        """
        # Validate account creation parameters
        validation = AccountValidator.validate_account_creation(
            account_number=account_number,
            customer_id=customer_id,
            account_type=account_type,
            currency=currency,
            initial_deposit=initial_deposit
        )
        
        if not validation["valid"]:
            return {
                "success": False,
                "message": "Invalid account parameters",
                "errors": validation["errors"]
            }
        
        # Check if account number already exists
        existing_account = self.account_repository.get_by_account_number(account_number)
        if existing_account:
            return {
                "success": False,
                "message": "Account number already exists",
                "errors": ["Account number already exists"]
            }
        
        # Map account type string to enum
        try:
            account_type_enum = AccountType[account_type.upper()]
        except (KeyError, ValueError):
            return {
                "success": False,
                "message": "Invalid account type",
                "errors": ["Invalid account type"]
            }
        
        # Create account entity
        account = Account(
            account_number=account_number,
            customer_id=UUID(customer_id),
            account_type=account_type_enum,
            balance=initial_deposit,
            status=AccountStatus.ACTIVE,
            currency=currency,
            interest_rate=interest_rate,
            overdraft_limit=overdraft_limit
        )
        
        # Save account to repository
        try:
            created_account = self.account_repository.create(account)
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to create account: {str(e)}",
                "errors": [str(e)]
            }
        
        # Send notification
        try:
            self.notification_service.send_account_status_notification(
                account_number=account_number,
                status="CREATED",
                timestamp=created_account.created_at.isoformat()
            )
        except Exception:
            # Don't fail the operation if notification fails
            pass
        
        return {
            "success": True,
            "message": "Account created successfully",
            "data": {
                "account_id": str(created_account.id),
                "account_number": created_account.account_number,
                "customer_id": str(created_account.customer_id),
                "account_type": created_account.account_type.value,
                "balance": str(created_account.balance),
                "currency": created_account.currency,
                "status": created_account.status.value,
                "created_at": created_account.created_at.isoformat()
            }
        }
