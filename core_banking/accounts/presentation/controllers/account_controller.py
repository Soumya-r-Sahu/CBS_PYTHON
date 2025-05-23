"""
Account Controller

This module provides controllers for handling account-related requests
in the presentation layer of the Core Banking module.
"""

import uuid
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional

from core_banking.accounts.domain.entities.account import Account, AccountType, AccountStatus
from core_banking.accounts.application.services.account_service import AccountService
from core_banking.utils.core_banking_utils import (
    ValidationException,
    BusinessRuleException,
    DatabaseException,
    MoneyUtility
)


class AccountController:
    """Controller for handling account-related requests"""
    
    def __init__(self, account_service: AccountService):
        """
        Initialize controller with account service
        
        Args:
            account_service: Service for account operations
        """
        self.account_service = account_service
        self.logger = logging.getLogger(__name__)
    
    def create_account(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new account
        
        Args:
            request_data: Dictionary containing account creation data
                - customer_id: ID of the customer
                - account_type: Type of account (SAVINGS, CURRENT, FIXED_DEPOSIT)
                - initial_deposit: Initial deposit amount (optional)
                - currency: Currency code (default: INR)
                - interest_rate: Interest rate for savings/fixed deposits (optional)
                - overdraft_limit: Overdraft limit for current accounts (optional)
                
        Returns:
            Response dictionary with created account or error details
        """
        try:
            # Extract and validate required parameters
            self._validate_request_parameters(request_data, ['customer_id', 'account_type'])
            
            customer_id = uuid.UUID(request_data['customer_id'])
            account_type = AccountType(request_data['account_type'])
            
            # Extract optional parameters with defaults
            initial_deposit = Decimal(str(request_data.get('initial_deposit', '0.00')))
            currency = request_data.get('currency', 'INR')
            
            # Type-specific parameters
            interest_rate = None
            if 'interest_rate' in request_data:
                interest_rate = Decimal(str(request_data['interest_rate']))
                
            overdraft_limit = None
            if 'overdraft_limit' in request_data:
                overdraft_limit = Decimal(str(request_data['overdraft_limit']))
            
            # Create account
            account = self.account_service.create_account(
                customer_id=customer_id,
                account_type=account_type,
                initial_deposit=initial_deposit,
                currency=currency,
                interest_rate=interest_rate,
                overdraft_limit=overdraft_limit
            )
            
            # Return success response
            return {
                'success': True,
                'message': f"{account_type.value} account created successfully",
                'account': self._format_account(account)
            }
            
        except (ValidationException, BusinessRuleException, DatabaseException) as e:
            self.logger.error(f"Error creating account: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'error_code': getattr(e, 'error_code', 'UNKNOWN_ERROR')
            }
        except Exception as e:
            self.logger.error(f"Unexpected error creating account: {str(e)}")
            return {
                'success': False,
                'message': f"An unexpected error occurred: {str(e)}",
                'error_code': 'SYSTEM_ERROR'
            }
    
    def get_account(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get account details by ID or account number
        
        Args:
            request_data: Dictionary containing request parameters
                - account_id: UUID of the account (optional if account_number provided)
                - account_number: Account number string (optional if account_id provided)
                
        Returns:
            Response dictionary with account details or error
        """
        try:
            # Check for either account_id or account_number
            if 'account_id' not in request_data and 'account_number' not in request_data:
                raise ValidationException(
                    "Either account_id or account_number must be provided", 
                    "MISSING_PARAMETER"
                )
            
            account = None
            
            # Get account by ID
            if 'account_id' in request_data:
                account_id = uuid.UUID(request_data['account_id'])
                account = self.account_service.get_account_by_id(account_id)
            
            # Get account by number
            elif 'account_number' in request_data:
                account_number = request_data['account_number']
                account = self.account_service.get_account_by_number(account_number)
            
            # Check if account was found
            if not account:
                return {
                    'success': False,
                    'message': "Account not found",
                    'error_code': 'ACCOUNT_NOT_FOUND'
                }
            
            # Return account details
            return {
                'success': True,
                'account': self._format_account(account)
            }
            
        except (ValidationException, BusinessRuleException, DatabaseException) as e:
            self.logger.error(f"Error retrieving account: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'error_code': getattr(e, 'error_code', 'UNKNOWN_ERROR')
            }
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving account: {str(e)}")
            return {
                'success': False,
                'message': f"An unexpected error occurred: {str(e)}",
                'error_code': 'SYSTEM_ERROR'
            }
    
    def get_customer_accounts(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get all accounts for a customer
        
        Args:
            request_data: Dictionary containing request parameters
                - customer_id: ID of the customer
                - account_type: Optional filter by account type
                - status: Optional filter by account status
                
        Returns:
            Response dictionary with list of accounts
        """
        try:
            # Extract and validate required parameters
            self._validate_request_parameters(request_data, ['customer_id'])
            
            customer_id = uuid.UUID(request_data['customer_id'])
            
            # Extract optional filters
            account_type = None
            if 'account_type' in request_data and request_data['account_type']:
                account_type = AccountType(request_data['account_type'])
                
            status = None
            if 'status' in request_data and request_data['status']:
                status = AccountStatus(request_data['status'])
            
            # Get accounts
            accounts = self.account_service.get_customer_accounts(
                customer_id=customer_id,
                account_type=account_type,
                status=status
            )
            
            # Format for response
            formatted_accounts = [self._format_account(account) for account in accounts]
            
            # Return success response
            return {
                'success': True,
                'customer_id': str(customer_id),
                'account_count': len(formatted_accounts),
                'accounts': formatted_accounts
            }
            
        except (ValidationException, BusinessRuleException, DatabaseException) as e:
            self.logger.error(f"Error retrieving customer accounts: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'error_code': getattr(e, 'error_code', 'UNKNOWN_ERROR')
            }
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving customer accounts: {str(e)}")
            return {
                'success': False,
                'message': f"An unexpected error occurred: {str(e)}",
                'error_code': 'SYSTEM_ERROR'
            }
    
    def update_account_status(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the status of an account
        
        Args:
            request_data: Dictionary containing request parameters
                - account_id: ID of the account
                - status: New status (ACTIVE, INACTIVE, BLOCKED, CLOSED)
                - reason: Reason for the status change
                
        Returns:
            Response dictionary with updated account
        """
        try:
            # Extract and validate required parameters
            self._validate_request_parameters(request_data, ['account_id', 'status', 'reason'])
            
            account_id = uuid.UUID(request_data['account_id'])
            status = AccountStatus(request_data['status'])
            reason = request_data['reason']
            
            # Update account status
            account = self.account_service.update_account_status(
                account_id=account_id,
                status=status,
                reason=reason
            )
            
            # Return success response
            return {
                'success': True,
                'message': f"Account status updated to {status.value}",
                'account': self._format_account(account)
            }
            
        except (ValidationException, BusinessRuleException, DatabaseException) as e:
            self.logger.error(f"Error updating account status: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'error_code': getattr(e, 'error_code', 'UNKNOWN_ERROR')
            }
        except Exception as e:
            self.logger.error(f"Unexpected error updating account status: {str(e)}")
            return {
                'success': False,
                'message': f"An unexpected error occurred: {str(e)}",
                'error_code': 'SYSTEM_ERROR'
            }
    
    def close_account(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Close an account
        
        Args:
            request_data: Dictionary containing request parameters
                - account_id: ID of the account
                - reason: Reason for closing the account
                - transfer_account_id: ID of account to transfer remaining balance (optional)
                
        Returns:
            Response dictionary with result of the operation
        """
        try:
            # Extract and validate required parameters
            self._validate_request_parameters(request_data, ['account_id', 'reason'])
            
            account_id = uuid.UUID(request_data['account_id'])
            reason = request_data['reason']
            
            # Get optional transfer account
            transfer_account_id = None
            if 'transfer_account_id' in request_data and request_data['transfer_account_id']:
                transfer_account_id = uuid.UUID(request_data['transfer_account_id'])
            
            # Close the account
            result = self.account_service.close_account(
                account_id=account_id,
                reason=reason,
                transfer_account_id=transfer_account_id
            )
            
            # Return success response
            return {
                'success': True,
                'message': f"Account closed successfully. {result['message']}",
                'closing_balance': str(result['closing_balance']),
                'formatted_balance': MoneyUtility.format_currency(
                    result['closing_balance'], 
                    result['currency']
                ),
                'transfer_transaction_id': result.get('transfer_transaction_id')
            }
            
        except (ValidationException, BusinessRuleException, DatabaseException) as e:
            self.logger.error(f"Error closing account: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'error_code': getattr(e, 'error_code', 'UNKNOWN_ERROR')
            }
        except Exception as e:
            self.logger.error(f"Unexpected error closing account: {str(e)}")
            return {
                'success': False,
                'message': f"An unexpected error occurred: {str(e)}",
                'error_code': 'SYSTEM_ERROR'
            }
    
    def _validate_request_parameters(self, request_data: Dict[str, Any], required_params: List[str]) -> None:
        """
        Validate that request contains all required parameters
        
        Args:
            request_data: Dictionary containing the request data
            required_params: List of required parameter names
            
        Raises:
            ValidationException: If any required parameter is missing
        """
        for param in required_params:
            if param not in request_data or request_data[param] is None:
                raise ValidationException(f"Missing required parameter: {param}", "MISSING_PARAMETER")
    
    def _format_account(self, account: Account) -> Dict[str, Any]:
        """
        Format account object for API response
        
        Args:
            account: Account entity
            
        Returns:
            Dictionary representation of account
        """
        return {
            'id': str(account.id),
            'account_number': account.account_number,
            'customer_id': str(account.customer_id),
            'account_type': account.account_type.value,
            'balance': str(account.balance),
            'formatted_balance': MoneyUtility.format_currency(account.balance, account.currency),
            'available_balance': str(self._calculate_available_balance(account)),
            'status': account.status.value,
            'currency': account.currency,
            'interest_rate': str(account.interest_rate) if account.interest_rate else None,
            'overdraft_limit': str(account.overdraft_limit) if account.overdraft_limit else None,
            'created_at': account.created_at.isoformat() if account.created_at else None,
            'updated_at': account.updated_at.isoformat() if account.updated_at else None
        }
    
    def _calculate_available_balance(self, account: Account) -> Decimal:
        """
        Calculate available balance including overdraft limit
        
        Args:
            account: Account entity
            
        Returns:
            Available balance as Decimal
        """
        if account.account_type == AccountType.CURRENT and account.overdraft_limit:
            return account.balance + account.overdraft_limit
        return account.balance
