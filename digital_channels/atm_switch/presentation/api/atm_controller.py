"""
ATM Controller

This module defines the API controller for the ATM-Switch module.
"""

import json
from decimal import Decimal
from typing import Dict, Any, Union
from datetime import datetime

from ...application.use_cases.withdraw_cash import WithdrawCashUseCase
from ...application.use_cases.check_balance import CheckBalanceUseCase
from ...application.use_cases.change_pin import ChangePinUseCase
from ...application.use_cases.get_mini_statement import GetMiniStatementUseCase
from ...application.use_cases.validate_card import ValidateCardUseCase


class AtmController:
    """API controller for ATM operations"""
    
    def __init__(
        self,
        withdraw_cash_use_case: WithdrawCashUseCase,
        check_balance_use_case: CheckBalanceUseCase,
        change_pin_use_case: ChangePinUseCase,
        get_mini_statement_use_case: GetMiniStatementUseCase,
        validate_card_use_case: ValidateCardUseCase
    ):
        """
        Initialize controller with use cases
        
        Args:
            withdraw_cash_use_case: Use case for withdrawing cash
            check_balance_use_case: Use case for checking balance
            change_pin_use_case: Use case for changing PIN
            get_mini_statement_use_case: Use case for getting mini statement
            validate_card_use_case: Use case for validating card
        """
        self.withdraw_cash_use_case = withdraw_cash_use_case
        self.check_balance_use_case = check_balance_use_case
        self.change_pin_use_case = change_pin_use_case
        self.get_mini_statement_use_case = get_mini_statement_use_case
        self.validate_card_use_case = validate_card_use_case
    
    def _decimal_encoder(self, obj: Any) -> Union[str, Any]:
        """
        Handle JSON encoding for Decimal and datetime objects
        
        Args:
            obj: Object to encode
            
        Returns:
            JSON-serializable object
        """
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def withdraw_cash(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle withdraw cash request
        
        Args:
            request: Request data containing session_token and amount
            
        Returns:
            Response data
        """
        try:
            session_token = request.get('session_token')
            amount = request.get('amount')
            
            if not session_token:
                return {
                    'status': 'error',
                    'message': 'Session token is required'
                }
            
            if not amount:
                return {
                    'status': 'error',
                    'message': 'Amount is required'
                }
            
            try:
                amount = Decimal(str(amount))
            except (ValueError, TypeError):
                return {
                    'status': 'error',
                    'message': 'Invalid amount format'
                }
            
            result = self.withdraw_cash_use_case.execute(session_token, amount)
            
            if result['success']:
                return {
                    'status': 'success',
                    'data': result
                }
            else:
                return {
                    'status': 'error',
                    'message': result['message']
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Internal error: {str(e)}'
            }
    
    def check_balance(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle check balance request
        
        Args:
            request: Request data containing session_token
            
        Returns:
            Response data
        """
        try:
            session_token = request.get('session_token')
            
            if not session_token:
                return {
                    'status': 'error',
                    'message': 'Session token is required'
                }
            
            result = self.check_balance_use_case.execute(session_token)
            
            if result['success']:
                return {
                    'status': 'success',
                    'data': result
                }
            else:
                return {
                    'status': 'error',
                    'message': result['message']
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Internal error: {str(e)}'
            }
    
    def change_pin(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle change PIN request
        
        Args:
            request: Request data containing session_token, current_pin, and new_pin
            
        Returns:
            Response data
        """
        try:
            session_token = request.get('session_token')
            current_pin = request.get('current_pin')
            new_pin = request.get('new_pin')
            
            if not all([session_token, current_pin, new_pin]):
                return {
                    'status': 'error',
                    'message': 'Session token, current PIN, and new PIN are required'
                }
            
            result = self.change_pin_use_case.execute(
                session_token, current_pin, new_pin
            )
            
            if result['success']:
                return {
                    'status': 'success',
                    'message': 'PIN changed successfully',
                    'data': {
                        'changed_at': datetime.now().isoformat()
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': result['message']
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Internal error: {str(e)}'
            }
    
    def get_mini_statement(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mini statement request
        
        Args:
            request: Request data containing session_token and limit
            
        Returns:
            Response data
        """
        try:
            session_token = request.get('session_token')
            limit = request.get('limit', 10)
            
            if not session_token:
                return {
                    'status': 'error',
                    'message': 'Session token is required'
                }
            
            try:
                limit = int(limit)
                if limit <= 0 or limit > 50:
                    limit = 10
            except (ValueError, TypeError):
                limit = 10
            
            result = self.get_mini_statement_use_case.execute(
                session_token, limit
            )
            
            if result['success']:
                return {
                    'status': 'success',
                    'data': result
                }
            else:
                return {
                    'status': 'error',
                    'message': result['message']
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Internal error: {str(e)}'
            }
    
    def validate_card(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle validate card request
        
        Args:
            request: Request data containing card_number and pin
            
        Returns:
            Response data with session_token if successful
        """
        try:
            card_number = request.get('card_number')
            pin = request.get('pin')
            
            if not all([card_number, pin]):
                return {
                    'status': 'error',
                    'message': 'Card number and PIN are required'
                }
            
            result = self.validate_card_use_case.execute(card_number, pin)
            
            if result['success']:
                return {
                    'status': 'success',
                    'data': {
                        'session_token': result['session_token'],
                        'expiry': result.get('expiry'),
                        'account_number': result.get('account_number')
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': result['message']
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Internal error: {str(e)}'
            }
    
    def to_json(self, data: Dict[str, Any]) -> str:
        """
        Convert response data to JSON string
        
        Args:
            data: Response data
            
        Returns:
            JSON string
        """
        return json.dumps(data, default=self._decimal_encoder)
