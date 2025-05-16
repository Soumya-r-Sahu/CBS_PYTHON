"""
Close Account Use Case

This module defines the use case for closing a bank account.
"""

from typing import Dict, Any
from uuid import UUID

from ...domain.entities.account import Account, AccountStatus
from ...domain.services.account_rules import AccountRules
from ..interfaces.account_repository import AccountRepository
from ..interfaces.notification_service import NotificationService


class CloseAccountUseCase:
    """
    Use case for closing a bank account
    
    This use case orchestrates the process of closing a bank account, checking business rules,
    updating the account status, and notifying the customer.
    """
    
    def __init__(
        self,
        account_repository: AccountRepository,
        notification_service: NotificationService,
        account_rules: AccountRules
    ):
        """
        Initialize the use case
        
        Args:
            account_repository: Repository for account data access
            notification_service: Service for sending notifications
            account_rules: Service for enforcing account rules
        """
        self.account_repository = account_repository
        self.notification_service = notification_service
        self.account_rules = account_rules
    
    def execute(
        self,
        account_id: UUID,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Execute the close account use case
        
        Args:
            account_id: ID of the account to close
            reason: Optional reason for closing the account
            
        Returns:
            Result dictionary with account details
            
        Raises:
            ValueError: If the account does not exist
            ValueError: If the account is already closed
            ValueError: If the account cannot be closed (e.g. has outstanding balance)
        """
        # Get the account
        account = self.account_repository.get_by_id(account_id)
        
        # Validate that the account exists
        self.account_rules.validate_account_exists(account)
        
        # Check if account is already closed
        if account.status == AccountStatus.CLOSED:
            raise ValueError("Account is already closed")
        
        # Check if the account can be closed based on business rules
        self.account_rules.can_close_account(account)
        
        try:
            # Close the account
            account.close(reason)
            
            # Update the account in the repository
            self.account_repository.update(account)
            
            # Send notification to the customer
            self.notification_service.send_account_closed_notification(
                account_id=account_id,
                reason=reason
            )
            
            # Return the result
            return {
                "success": True,
                "account_id": str(account_id),
                "status": account.status.value,
                "closed_at": account.updated_at.isoformat()
            }
            
        except ValueError as e:
            # Return error result
            return {
                "success": False,
                "error": str(e),
                "account_id": str(account_id)
            }
