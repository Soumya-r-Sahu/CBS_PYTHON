"""
Transaction Controller

This module provides controllers for handling transaction-related requests
in the presentation layer, interacting with the application services.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
import uuid
import logging
import json

from core_banking.transactions.application.services.transaction_service import TransactionService
from core_banking.transactions.domain.entities.transaction import TransactionStatus, TransactionType
from core_banking.utils.core_banking_utils import (
    ValidationException,
    BusinessRuleException,
    DatabaseException,
    MoneyUtility
)


class TransactionController:
    """Controller for handling transaction-related requests"""
    
    def __init__(self, transaction_service: TransactionService):
        """
        Initialize the controller
        
        Args:
            transaction_service: Service for processing transactions
        """
        self.transaction_service = transaction_service
        self.logger = logging.getLogger(__name__)
    
    def process_deposit(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a deposit request
        
        Args:
            request_data: Dictionary containing the request data
                - account_id: ID of the account to deposit into
                - amount: Amount to deposit
                - description: Description of the transaction
                - reference_number: Optional reference number
                - processed_by: Optional user processing the transaction
                
        Returns:
            Response dictionary
        """
        try:
            # Extract and validate request parameters
            self._validate_request_parameters(request_data, ['account_id', 'amount', 'description'])
            
            account_id = uuid.UUID(request_data['account_id'])
            amount = Decimal(str(request_data['amount']))
            description = request_data['description']
            reference_number = request_data.get('reference_number')
            processed_by = request_data.get('processed_by')
            
            # Process deposit
            transaction = self.transaction_service.deposit(
                account_id=account_id,
                amount=amount,
                description=description,
                reference_number=reference_number,
                processed_by=processed_by
            )
            
            # Return success response
            return {
                'success': True,
                'message': f"Deposit of {MoneyUtility.format_currency(amount, transaction.currency)} processed successfully",
                'transaction': self._format_transaction(transaction)
            }
            
        except (ValidationException, BusinessRuleException, DatabaseException) as e:
            self.logger.error(f"Error processing deposit: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'error_code': getattr(e, 'error_code', 'UNKNOWN_ERROR')
            }
        except Exception as e:
            self.logger.error(f"Unexpected error processing deposit: {str(e)}")
            return {
                'success': False,
                'message': f"An unexpected error occurred: {str(e)}",
                'error_code': 'SYSTEM_ERROR'
            }
    
    def process_withdrawal(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a withdrawal request
        
        Args:
            request_data: Dictionary containing the request data
                - account_id: ID of the account to withdraw from
                - amount: Amount to withdraw
                - description: Description of the transaction
                - reference_number: Optional reference number
                - processed_by: Optional user processing the transaction
                
        Returns:
            Response dictionary
        """
        try:
            # Extract and validate request parameters
            self._validate_request_parameters(request_data, ['account_id', 'amount', 'description'])
            
            account_id = uuid.UUID(request_data['account_id'])
            amount = Decimal(str(request_data['amount']))
            description = request_data['description']
            reference_number = request_data.get('reference_number')
            processed_by = request_data.get('processed_by')
            
            # Process withdrawal
            transaction = self.transaction_service.withdraw(
                account_id=account_id,
                amount=amount,
                description=description,
                reference_number=reference_number,
                processed_by=processed_by
            )
            
            # Return success response
            return {
                'success': True,
                'message': f"Withdrawal of {MoneyUtility.format_currency(amount, transaction.currency)} processed successfully",
                'transaction': self._format_transaction(transaction)
            }
            
        except (ValidationException, BusinessRuleException, DatabaseException) as e:
            self.logger.error(f"Error processing withdrawal: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'error_code': getattr(e, 'error_code', 'UNKNOWN_ERROR')
            }
        except Exception as e:
            self.logger.error(f"Unexpected error processing withdrawal: {str(e)}")
            return {
                'success': False,
                'message': f"An unexpected error occurred: {str(e)}",
                'error_code': 'SYSTEM_ERROR'
            }
    
    def process_transfer(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a transfer request
        
        Args:
            request_data: Dictionary containing the request data
                - source_account_id: ID of the source account
                - destination_account_id: ID of the destination account
                - amount: Amount to transfer
                - description: Description of the transaction
                - reference_number: Optional reference number
                - processed_by: Optional user processing the transaction
                
        Returns:
            Response dictionary
        """
        try:
            # Extract and validate request parameters
            self._validate_request_parameters(
                request_data, 
                ['source_account_id', 'destination_account_id', 'amount', 'description']
            )
            
            source_account_id = uuid.UUID(request_data['source_account_id'])
            destination_account_id = uuid.UUID(request_data['destination_account_id'])
            amount = Decimal(str(request_data['amount']))
            description = request_data['description']
            reference_number = request_data.get('reference_number')
            processed_by = request_data.get('processed_by')
            
            # Process transfer
            source_transaction, dest_transaction = self.transaction_service.transfer(
                source_account_id=source_account_id,
                destination_account_id=destination_account_id,
                amount=amount,
                description=description,
                reference_number=reference_number,
                processed_by=processed_by
            )
            
            # Return success response
            return {
                'success': True,
                'message': f"Transfer of {MoneyUtility.format_currency(amount, source_transaction.currency)} processed successfully",
                'source_transaction': self._format_transaction(source_transaction),
                'destination_transaction': self._format_transaction(dest_transaction),
                'reference_number': source_transaction.reference_number
            }
            
        except (ValidationException, BusinessRuleException, DatabaseException) as e:
            self.logger.error(f"Error processing transfer: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'error_code': getattr(e, 'error_code', 'UNKNOWN_ERROR')
            }
        except Exception as e:
            self.logger.error(f"Unexpected error processing transfer: {str(e)}")
            return {
                'success': False,
                'message': f"An unexpected error occurred: {str(e)}",
                'error_code': 'SYSTEM_ERROR'
            }
    
    def get_transaction_history(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get transaction history for an account
        
        Args:
            request_data: Dictionary containing the request data
                - account_id: ID of the account
                - start_date: Optional start date (ISO format)
                - end_date: Optional end date (ISO format)
                - transaction_type: Optional transaction type
                - status: Optional transaction status
                - limit: Optional max number of transactions (default: 100)
                - offset: Optional number of transactions to skip (default: 0)
                
        Returns:
            Response dictionary with transaction history
        """
        try:
            # Extract and validate request parameters
            self._validate_request_parameters(request_data, ['account_id'])
            
            account_id = uuid.UUID(request_data['account_id'])
            
            # Parse optional parameters
            start_date = None
            if 'start_date' in request_data and request_data['start_date']:
                start_date = datetime.fromisoformat(request_data['start_date'])
                
            end_date = None
            if 'end_date' in request_data and request_data['end_date']:
                end_date = datetime.fromisoformat(request_data['end_date'])
                
            transaction_type = None
            if 'transaction_type' in request_data and request_data['transaction_type']:
                transaction_type = TransactionType(request_data['transaction_type'])
                
            status = None
            if 'status' in request_data and request_data['status']:
                status = TransactionStatus(request_data['status'])
                
            limit = int(request_data.get('limit', 100))
            offset = int(request_data.get('offset', 0))
            
            # Get transaction history
            transactions = self.transaction_service.get_transaction_history(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
                transaction_type=transaction_type,
                status=status,
                limit=limit,
                offset=offset
            )
            
            # Format transactions for response
            formatted_transactions = [self._format_transaction(tx) for tx in transactions]
            
            # Return success response
            return {
                'success': True,
                'transactions': formatted_transactions,
                'count': len(formatted_transactions),
                'limit': limit,
                'offset': offset
            }
            
        except (ValidationException, BusinessRuleException, DatabaseException) as e:
            self.logger.error(f"Error retrieving transaction history: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'error_code': getattr(e, 'error_code', 'UNKNOWN_ERROR')
            }
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving transaction history: {str(e)}")
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
    
    def _format_transaction(self, transaction) -> Dict[str, Any]:
        """
        Format transaction object for API response
        
        Args:
            transaction: Transaction entity
            
        Returns:
            Dictionary representation of transaction
        """
        return {
            'id': str(transaction.id),
            'transaction_id': transaction.transaction_id,
            'account_id': str(transaction.account_id),
            'amount': str(transaction.amount),
            'formatted_amount': MoneyUtility.format_currency(transaction.amount, transaction.currency),
            'transaction_type': transaction.transaction_type.value,
            'description': transaction.description,
            'status': transaction.status.value,
            'timestamp': transaction.timestamp.isoformat() if transaction.timestamp else None,
            'reference_number': transaction.reference_number,
            'source_account_id': str(transaction.source_account_id) if transaction.source_account_id else None,
            'destination_account_id': str(transaction.destination_account_id) if transaction.destination_account_id else None,
            'processed_by': transaction.processed_by,
            'processing_date': transaction.processing_date.isoformat() if transaction.processing_date else None,
            'currency': transaction.currency
        }
