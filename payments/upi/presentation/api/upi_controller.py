"""
UPI API controller for handling UPI payment requests.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from flask import Blueprint, request, jsonify

from ...application.use_cases.send_money_use_case import SendMoneyUseCase, SendMoneyRequest
from ...application.use_cases.complete_transaction_use_case import CompleteTransactionUseCase, CompleteTransactionRequest


class UpiController:
    """API controller for UPI transactions."""
    
    def __init__(
        self,
        send_money_use_case: SendMoneyUseCase,
        complete_transaction_use_case: CompleteTransactionUseCase
    ):
        """
        Initialize with required use cases.
        
        Args:
            send_money_use_case: Use case for sending money
            complete_transaction_use_case: Use case for completing transactions
        """
        self.send_money_use_case = send_money_use_case
        self.complete_transaction_use_case = complete_transaction_use_case
        
        # Create Flask Blueprint
        self.blueprint = Blueprint('upi', __name__)
        
        # Register routes
        self.blueprint.route('/send-money', methods=['POST'])(self.send_money)
        self.blueprint.route('/complete-transaction', methods=['POST'])(self.complete_transaction)
        self.blueprint.route('/transaction/<transaction_id>', methods=['GET'])(self.get_transaction)
    
    def send_money(self):
        """Handle send money API request."""
        try:
            data = request.json
            
            # Validate request data
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid request data'
                }), 400
            
            # Extract request data
            sender_vpa = data.get('sender_vpa')
            receiver_vpa = data.get('receiver_vpa')
            amount = data.get('amount')
            remarks = data.get('remarks')
            
            # Validate required fields
            if not sender_vpa or not receiver_vpa or not amount:
                return jsonify({
                    'success': False,
                    'error': 'Missing required fields'
                }), 400
            
            # Convert amount to float if needed
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Invalid amount format'
                }), 400
            
            # Create use case request
            send_money_request = SendMoneyRequest(
                sender_vpa=sender_vpa,
                receiver_vpa=receiver_vpa,
                amount=amount,
                remarks=remarks
            )
            
            # Execute use case
            response = self.send_money_use_case.execute(send_money_request)
            
            # Return response
            if response.success:
                return jsonify({
                    'success': True,
                    'message': response.message,
                    'transaction_id': str(response.transaction_id)
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': response.message,
                    'error_code': response.error_code
                }), 400
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500
    
    def complete_transaction(self):
        """Handle complete transaction API request."""
        try:
            data = request.json
            
            # Validate request data
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid request data'
                }), 400
            
            # Extract request data
            transaction_id = data.get('transaction_id')
            reference_id = data.get('reference_id')
            
            # Validate required fields
            if not transaction_id or not reference_id:
                return jsonify({
                    'success': False,
                    'error': 'Missing required fields'
                }), 400
            
            # Convert transaction_id to UUID
            try:
                transaction_id = UUID(transaction_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid transaction ID format'
                }), 400
            
            # Create use case request
            complete_request = CompleteTransactionRequest(
                transaction_id=transaction_id,
                reference_id=reference_id
            )
            
            # Execute use case
            response = self.complete_transaction_use_case.execute(complete_request)
            
            # Return response
            if response.success:
                return jsonify({
                    'success': True,
                    'message': response.message
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': response.message,
                    'error_code': response.error_code
                }), 400
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500
    
    def get_transaction(self, transaction_id):
        """
        Handle get transaction API request.
        
        This is a placeholder. In a real implementation, this would use a dedicated use case.
        """
        try:
            # Convert transaction_id to UUID
            try:
                transaction_id = UUID(transaction_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid transaction ID format'
                }), 400
            
            # This is a placeholder. In a real implementation,
            # this would use a GetTransactionUseCase
            return jsonify({
                'success': False,
                'error': 'Not implemented yet'
            }), 501
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500
